import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate

from ledgerx import shared
from ledgerx_realestate.engine import accounting, logic


def daily():
	for fn in (expire_reservations, due_commissions, bill_rentals, end_leases):
		try:
			fn()
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Real estate daily task failed: {fn.__name__}")


def expire_reservations():
	"""A reservation past its date frees the unit. The deposit stays as the customer's credit."""
	names = frappe.get_all("Unit Reservation", filters={"status": "Active", "valid_until": ["<", nowdate()]}, pluck="name")
	shared.run_each(names, lambda r: frappe.get_doc("Unit Reservation", r)._free("Expired"), "Reservation expiry failed")


def due_commissions():
	"""A commission becomes due once the customer has paid the share set in the settings."""
	pct = flt(accounting.settings().commission_due_pct)

	def check(c):
		inv = frappe.db.get_value("Unit Contract", c.contract, "sales_invoice")
		if inv and logic.commission_due(accounting.collected_pct(inv), 100, pct):
			frappe.db.set_value("Sales Commission", c.name, "status", "Due")

	shared.run_each(frappe.get_all("Sales Commission", filters={"status": "Pending"}, fields=["name", "contract"]), check, "Commission due check failed")


def bill_rentals():
	names = frappe.get_all("Property Rental Contract", filters={"status": "Active"}, pluck="name")
	shared.run_each(names, lambda r: frappe.get_doc("Property Rental Contract", r).bill_due(), "Rent billing failed")


def _end_lease(name):
	d = frappe.get_doc("Property Rental Contract", name)
	d.bill_due()
	d.end_lease()


def end_leases():
	"""A lease past its end date is billed to its end and closed, and the unit is freed."""
	names = frappe.get_all("Property Rental Contract", filters={"status": "Active", "end_date": ["<", nowdate()]}, pluck="name")
	shared.run_each(names, _end_lease, "Lease end failed")


def charge_late_fees():
	"""Monthly: one invoice per contract for the late fee on what is overdue, if the settings charge one."""
	s = accounting.settings()
	pct = flt(s.late_fee_pct)
	if pct <= 0:
		return
	today = getdate(nowdate())
	for name in frappe.get_all("Unit Contract", filters={"status": ["in", ["Active", "Delivered"]]}, pluck="name"):
		try:
			c = frappe.get_doc("Unit Contract", name)
			if any(getdate(l.fee_date).replace(day=1) == today.replace(day=1) for l in c.late_fees):
				continue
			rows = accounting.invoice_state(c.sales_invoice)["rows"]
			overdue = sum(flt(r.payment_amount) - flt(r.paid_amount) for r in rows
				if flt(r.payment_amount) - flt(r.paid_amount) > 0.005 and (today - getdate(r.due_date)).days > int(s.grace_days or 0))
			fee = logic.late_fee(overdue, 1, pct)
			if fee <= 0:
				continue
			inv = accounting.sales_invoice(c.customer, [(accounting.item("Late Fee"), fee, accounting.need(s, "late_fee_income_account", "Late Fee Income Account"),
				_("Late fee {0} - {1}").format(today.strftime("%Y-%m"), c.unit))], accounting.cost_center_of(c.project), _("Late fee - contract {0}").format(c.name))
			c.append("late_fees", {"fee_date": today, "base": overdue, "fee": fee, "sales_invoice": inv})
			c.save(ignore_permissions=True)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Late fee failed for contract {name}")
