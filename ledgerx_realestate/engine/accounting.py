"""Customers, suppliers, invoices and payments of the real estate module, all on ERPNext's own documents."""
import frappe
from frappe import _
from frappe.utils import flt, nowdate

from ledgerx_realestate.engine import logic


def settings():
	return frappe.get_cached_doc("Real Estate Settings")


def need(s, field, label):
	if not s.get(field):
		frappe.throw(_("Set {0} in Real Estate Settings first").format(_(label)))
	return s.get(field)


def cost_center_of(project):
	return frappe.db.get_value("Real Estate Project", project, "cost_center") if project else None


def item(code, group=None):
	"""A service item used on invoices (created on first use)."""
	if not frappe.db.exists("Item", code):
		grp = group or ("Services" if frappe.db.exists("Item Group", "Services") else "All Item Groups")
		uom = "Nos" if frappe.db.exists("UOM", "Nos") else frappe.db.get_value("UOM", {}, "name")
		frappe.get_doc({"doctype": "Item", "item_code": code, "item_name": code, "item_group": grp, "stock_uom": uom, "is_stock_item": 0,
			"is_sales_item": 1, "is_purchase_item": 1, "include_item_in_manufacturing": 0}).insert(ignore_permissions=True)
	return code


def money_account(mode_of_payment):
	from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account

	acc = (get_bank_cash_account(mode_of_payment, settings().company) or {}).get("account")
	if not acc:
		frappe.throw(_("Mode of Payment {0} has no account for the company").format(mode_of_payment))
	return acc


def payment(customer, amount, account, invoice=None, remarks="", refund=False, reference=None):
	"""Receive money from a customer (or pay it back). With an invoice the amount is allocated to it."""
	from erpnext.accounts.party import get_party_account

	company = settings().company
	receivable = get_party_account("Customer", customer, company)
	amount = flt(amount)
	pe = frappe.new_doc("Payment Entry")
	pe.update({"payment_type": "Pay" if refund else "Receive", "company": company, "posting_date": nowdate(), "party_type": "Customer",
		"party": customer, "remarks": remarks, "reference_no": reference or remarks[:40] or "-", "reference_date": nowdate()})
	if refund:
		pe.update({"paid_from": account, "paid_to": receivable, "paid_amount": amount, "received_amount": amount})
	else:
		pe.update({"paid_from": receivable, "paid_to": account, "paid_amount": amount, "received_amount": logic.r2(amount)})
	if invoice:
		pe.append("references", {"reference_doctype": "Sales Invoice", "reference_name": invoice, "allocated_amount": amount})
	pe.insert(ignore_permissions=True)
	pe.submit()
	return pe.name


def supplier_payment(supplier, amount, account, remarks=""):
	"""Money paid to a supplier in advance (an advance to a contractor)."""
	from erpnext.accounts.party import get_party_account

	company = settings().company
	pe = frappe.new_doc("Payment Entry")
	pe.update({"payment_type": "Pay", "company": company, "posting_date": nowdate(), "party_type": "Supplier", "party": supplier, "remarks": remarks,
		"reference_no": remarks[:40] or "-", "reference_date": nowdate(), "paid_from": account,
		"paid_to": get_party_account("Supplier", supplier, company), "paid_amount": flt(amount), "received_amount": flt(amount)})
	pe.insert(ignore_permissions=True)
	pe.submit()
	return pe.name


def sales_invoice(customer, lines, cost_center, remarks, due_date=None, schedule=None, vat=0, apply_advances=False, posting_date=None):
	"""lines: (item_code, amount, income_account, description). One submitted invoice; returns its name."""
	s = settings()
	inv = frappe.new_doc("Sales Invoice")
	inv.update({"customer": customer, "company": s.company, "posting_date": posting_date or nowdate(), "due_date": due_date or posting_date or nowdate(),
		"cost_center": cost_center, "update_stock": 0, "ignore_pricing_rule": 1, "allocate_advances_automatically": 1 if apply_advances else 0,
		"selling_price_list": frappe.db.get_value("Price List", {"selling": 1, "enabled": 1}, "name"), "remarks": remarks})
	for code, amount, account, desc in lines:
		inv.append("items", {"item_code": code, "qty": 1, "rate": flt(amount), "income_account": account, "cost_center": cost_center, "description": desc})
	if flt(vat):
		inv.append("taxes", {"charge_type": "Actual", "account_head": need(s, "vat_account", "VAT Account"), "description": _("VAT"), "tax_amount": flt(vat),
			"cost_center": cost_center})
	for due, amount in schedule or []:
		inv.append("payment_schedule", {"due_date": due, "payment_amount": amount, "invoice_portion": 0})
	inv.insert(ignore_permissions=True)
	if apply_advances:
		inv.set_advances()
		if inv.get("advances"):
			inv.save(ignore_permissions=True)
	inv.submit()
	return inv.name


def invoice_state(invoice):
	"""total, outstanding and the unpaid schedule rows of a contract invoice."""
	if not invoice:
		return {"total": 0, "outstanding": 0, "rows": []}
	d = frappe.db.get_value("Sales Invoice", invoice, ["grand_total", "outstanding_amount"], as_dict=True)
	rows = frappe.get_all("Payment Schedule", filters={"parent": invoice, "parenttype": "Sales Invoice"}, fields=["due_date", "payment_amount", "paid_amount"],
		order_by="due_date")
	return {"total": flt(d.grand_total), "outstanding": flt(d.outstanding_amount), "rows": rows}


def collected_pct(invoice):
	st = invoice_state(invoice)
	return (st["total"] - st["outstanding"]) * 100 / st["total"] if st["total"] else 0
