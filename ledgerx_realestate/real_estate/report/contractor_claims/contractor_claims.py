import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	f = {"status": "Approved"}
	for k in ("project", "contractor"):
		if filters.get(k):
			f[k] = filters[k]
	cols = [
		{"label": _("Contractor"), "fieldname": "contractor", "fieldtype": "Link", "options": "Supplier", "width": 170},
		{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Real Estate Project", "width": 140},
		{"label": _("Construction Contract"), "fieldname": "construction_contract", "fieldtype": "Link", "options": "Construction Contract", "width": 160},
		{"label": _("Claims"), "fieldname": "claims", "fieldtype": "Int", "width": 70},
		{"label": _("Claimed"), "fieldname": "gross", "fieldtype": "Currency", "width": 130},
		{"label": _("Retention"), "fieldname": "retention", "fieldtype": "Currency", "width": 120},
		{"label": _("Advance Recovered"), "fieldname": "advance_recovery", "fieldtype": "Currency", "width": 130},
		{"label": _("Net Payable"), "fieldname": "net", "fieldtype": "Currency", "width": 130},
		{"label": _("Contract Value"), "fieldname": "contract_value", "fieldtype": "Currency", "width": 130},
		{"label": _("Completion (%)"), "fieldname": "pct", "fieldtype": "Percent", "width": 110},
	]
	rows = frappe.get_all("Progress Claim", filters=f, fields=["contractor", "project", "construction_contract", "count(name) as claims", "sum(gross) as gross", "sum(retention) as retention",
		"sum(advance_recovery) as advance_recovery", "sum(net) as net", "max(contract_value) as contract_value", "max(cumulative_pct) as pct"],
		group_by="contractor, project, construction_contract", order_by="contractor")
	return cols, rows
