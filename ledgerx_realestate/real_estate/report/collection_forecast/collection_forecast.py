import frappe
from frappe import _
from frappe.utils import add_months, nowdate


def execute(filters=None):
	"""What is still due to be collected, month by month: the cash the project can expect."""
	filters = filters or {}
	args = [filters.get("from_date") or nowdate(), filters.get("to_date") or add_months(nowdate(), 12)]
	cond = ""
	if filters.get("project"):
		cond = " and c.project = %s"
		args.append(filters["project"])
	rows = frappe.db.sql(
		f"""select date_format(p.due_date, '%%Y-%%m') as month, count(*) as installments, sum(p.payment_amount - p.paid_amount) as due
		from `tabPayment Schedule` p join `tabSales Invoice` i on i.name = p.parent join `tabUnit Contract` c on c.sales_invoice = i.name
		where p.parenttype = 'Sales Invoice' and i.docstatus = 1 and c.status in ('Active', 'Delivered') and p.payment_amount - p.paid_amount > 0.005
		and p.due_date between %s and %s {cond} group by month order by month""", args, as_dict=True)
	cols = [
		{"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 100},
		{"label": _("Installments"), "fieldname": "installments", "fieldtype": "Int", "width": 100},
		{"label": _("Expected Collection"), "fieldname": "due", "fieldtype": "Currency", "width": 160},
	]
	chart = {"data": {"labels": [r.month for r in rows], "datasets": [{"name": _("Expected Collection"), "values": [r.due or 0 for r in rows]}]}, "type": "bar"}
	return cols, rows, None, chart
