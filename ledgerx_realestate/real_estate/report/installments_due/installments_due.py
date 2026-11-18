import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate


def execute(filters=None):
	"""Every unpaid installment of a contract invoice, oldest first. Late ones show how many days."""
	filters = filters or {}
	args = [filters.get("until") or add_days(nowdate(), 30)]
	cond = ""
	if filters.get("project"):
		cond = " and c.project = %s"
		args.append(filters["project"])
	rows = frappe.db.sql(
		f"""select p.due_date, p.payment_amount - p.paid_amount as due, c.customer, c.unit, c.project, c.name as contract, i.name as invoice,
		(select mobile_no from `tabCustomer` where name = c.customer) as phone
		from `tabPayment Schedule` p join `tabSales Invoice` i on i.name = p.parent join `tabUnit Contract` c on c.sales_invoice = i.name
		where p.parenttype = 'Sales Invoice' and i.docstatus = 1 and c.status in ('Active', 'Delivered') and p.payment_amount - p.paid_amount > 0.005
		and p.due_date <= %s {cond} order by p.due_date""", args, as_dict=True)
	today = getdate(nowdate())
	for r in rows:
		r["late_days"] = max((today - getdate(r.due_date)).days, 0)
	cols = [
		{"label": _("Due Date"), "fieldname": "due_date", "fieldtype": "Date", "width": 100},
		{"label": _("Days Late"), "fieldname": "late_days", "fieldtype": "Int", "width": 80},
		{"label": _("Amount Due"), "fieldname": "due", "fieldtype": "Currency", "width": 130},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 170},
		{"label": _("Phone"), "fieldname": "phone", "fieldtype": "Data", "width": 110},
		{"label": _("Unit"), "fieldname": "unit", "fieldtype": "Link", "options": "Property Unit", "width": 140},
		{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Real Estate Project", "width": 130},
		{"label": _("Contract"), "fieldname": "contract", "fieldtype": "Link", "options": "Unit Contract", "width": 150},
	]
	return cols, rows
