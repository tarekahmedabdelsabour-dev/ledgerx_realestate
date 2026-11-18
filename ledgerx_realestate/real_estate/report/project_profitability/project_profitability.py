import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	"""Per project: sold value, collected, what was spent (everything posted to the project's cost center) and the margin."""
	filters = filters or {}
	rows = []
	for p in frappe.get_all("Real Estate Project", filters={"name": filters["project"]} if filters.get("project") else {}, fields=["name", "cost_center", "sales_target"]):
		units = frappe.db.count("Property Unit", {"project": p.name})
		sold = frappe.db.count("Property Unit", {"project": p.name, "status": ["in", ["Contracted", "Delivered"]]})
		c = frappe.db.sql("""select sum(c.price), sum(i.grand_total - i.outstanding_amount) from `tabUnit Contract` c
			left join `tabSales Invoice` i on i.name = c.sales_invoice and i.docstatus = 1 where c.project = %s and c.status in ('Active', 'Delivered')""", p.name)[0]
		spent = frappe.db.sql("""select sum(g.debit - g.credit) from `tabGL Entry` g join `tabAccount` a on a.name = g.account
			where g.cost_center = %s and g.is_cancelled = 0 and a.root_type in ('Expense')""", p.cost_center)[0][0]
		claimed = frappe.db.sql("""select sum(gross) from `tabProgress Claim` where project = %s and status = 'Approved'""", p.name)[0][0]
		sales, collected = flt(c[0]), flt(c[1])
		rows.append({"project": p.name, "units": units, "sold": sold, "sales": sales, "collected": collected, "claims": flt(claimed), "spent": flt(spent),
			"margin": sales - flt(spent), "target": flt(p.sales_target), "target_pct": round(sales * 100 / p.sales_target, 1) if p.sales_target else 0})
	cols = [
		{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Real Estate Project", "width": 170},
		{"label": _("Units"), "fieldname": "units", "fieldtype": "Int", "width": 70},
		{"label": _("Sold"), "fieldname": "sold", "fieldtype": "Int", "width": 70},
		{"label": _("Contracts Value"), "fieldname": "sales", "fieldtype": "Currency", "width": 140},
		{"label": _("Collected"), "fieldname": "collected", "fieldtype": "Currency", "width": 140},
		{"label": _("Contractor Claims"), "fieldname": "claims", "fieldtype": "Currency", "width": 140},
		{"label": _("Spent (Expenses)"), "fieldname": "spent", "fieldtype": "Currency", "width": 140},
		{"label": _("Margin"), "fieldname": "margin", "fieldtype": "Currency", "width": 140},
		{"label": _("Sales Target"), "fieldname": "target", "fieldtype": "Currency", "width": 130},
		{"label": _("Target Reached (%)"), "fieldname": "target_pct", "fieldtype": "Percent", "width": 120},
	]
	return cols, rows
