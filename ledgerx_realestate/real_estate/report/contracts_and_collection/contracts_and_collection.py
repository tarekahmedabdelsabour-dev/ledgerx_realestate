import frappe
from frappe import _
from frappe.utils import add_days, nowdate


def execute(filters=None):
	filters = filters or {}
	args = [filters.get("from_date") or add_days(nowdate(), -364), filters.get("to_date") or nowdate()]
	cond = ""
	for k in ("project", "broker", "salesman"):
		if filters.get(k):
			cond += f" and c.{k} = %s"
			args.append(filters[k])
	rows = frappe.db.sql(
		f"""select c.name, c.contract_date, c.project, c.unit, c.customer, c.salesman, c.broker, c.status, c.price, i.grand_total as invoiced,
		i.grand_total - i.outstanding_amount as collected, i.outstanding_amount as due
		from `tabUnit Contract` c left join `tabSales Invoice` i on i.name = c.sales_invoice and i.docstatus = 1
		where c.status in ('Active', 'Delivered') and c.contract_date between %s and %s {cond} order by c.contract_date desc""", args, as_dict=True)
	for r in rows:
		r["rate"] = round((r.collected or 0) * 100 / r.invoiced, 1) if r.invoiced else 0
	cols = [
		{"label": _("Contract"), "fieldname": "name", "fieldtype": "Link", "options": "Unit Contract", "width": 150},
		{"label": _("Date"), "fieldname": "contract_date", "fieldtype": "Date", "width": 95},
		{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Real Estate Project", "width": 130},
		{"label": _("Unit"), "fieldname": "unit", "fieldtype": "Link", "options": "Property Unit", "width": 140},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 160},
		{"label": _("Broker"), "fieldname": "broker", "fieldtype": "Link", "options": "Real Estate Broker", "width": 120},
		{"label": _("Contract Price"), "fieldname": "price", "fieldtype": "Currency", "width": 130},
		{"label": _("Invoiced"), "fieldname": "invoiced", "fieldtype": "Currency", "width": 130},
		{"label": _("Collected"), "fieldname": "collected", "fieldtype": "Currency", "width": 130},
		{"label": _("Still Due"), "fieldname": "due", "fieldtype": "Currency", "width": 130},
		{"label": _("Collected (%)"), "fieldname": "rate", "fieldtype": "Percent", "width": 100},
	]
	return cols, rows
