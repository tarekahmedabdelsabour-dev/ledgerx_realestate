import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	f = {k: filters[k] for k in ("project", "status", "category", "building") if filters.get(k)}
	cols = [
		{"label": _("Unit"), "fieldname": "name", "fieldtype": "Link", "options": "Property Unit", "width": 150},
		{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Real Estate Project", "width": 140},
		{"label": _("Building"), "fieldname": "building", "fieldtype": "Link", "options": "Building", "width": 120},
		{"label": _("Floor"), "fieldname": "floor", "fieldtype": "Int", "width": 55},
		{"label": _("Category"), "fieldname": "category", "fieldtype": "Data", "width": 90},
		{"label": _("Built Area (m²)"), "fieldname": "area_built", "fieldtype": "Float", "width": 100},
		{"label": _("Bedrooms"), "fieldname": "bedrooms", "fieldtype": "Int", "width": 80},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
		{"label": _("Price"), "fieldname": "list_price", "fieldtype": "Currency", "width": 120},
		{"label": _("Price per m²"), "fieldname": "per_m2", "fieldtype": "Currency", "width": 110},
		{"label": _("Owner"), "fieldname": "owner_customer", "fieldtype": "Link", "options": "Customer", "width": 150},
	]
	rows = frappe.get_all("Property Unit", filters=f, fields=[c["fieldname"] for c in cols if c["fieldname"] != "per_m2"], order_by="project, building, floor, name")
	for r in rows:
		r["per_m2"] = round((r.list_price or 0) / r.area_built, 2) if r.area_built else 0
	by = {}
	for r in rows:
		by[r.status] = by.get(r.status, 0) + 1
	chart = {"data": {"labels": [_(k) for k in by], "datasets": [{"values": list(by.values())}]}, "type": "donut"}
	return cols, rows, None, chart
