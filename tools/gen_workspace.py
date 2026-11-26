"""Writes the workspace, sidebar and dock JSON of ledgerx_realestate. Run from the repo root."""
import json
import os
import uuid

BASE = os.path.join(os.path.dirname(__file__), "..", "ledgerx_realestate")
TS = "2026-11-18 05:00:00.000000"  # raise this whenever the workspace changes: migrate only re-reads a file that is newer than the saved one
CARDS = [  # (label, doctype, filters, function, fn_field)
	("Available Units", "Property Unit", [["Property Unit", "status", "=", "Available"]], "Count", None),
	("Reserved Units", "Property Unit", [["Property Unit", "status", "=", "Reserved"]], "Count", None),
	("Active Contracts", "Unit Contract", [["Unit Contract", "status", "=", "Active"]], "Count", None),
	("Draft Contracts", "Unit Contract", [["Unit Contract", "status", "=", "Draft"]], "Count", None),
	("Cheques to Deposit", "Post Dated Cheque", [["Post Dated Cheque", "status", "=", "Received"]], "Count", None),
	("Commissions Due", "Sales Commission", [["Sales Commission", "status", "=", "Due"]], "Count", None),
	("Open Maintenance", "Property Maintenance Request", [["Property Maintenance Request", "status", "in", ["New", "Assigned", "In Progress"]]], "Count", None),
	("Active Leases", "Property Rental Contract", [["Property Rental Contract", "status", "=", "Active"]], "Count", None),
]
CHARTS = [  # (name, doctype, type, kind, extra)
	("Units by Status", "Property Unit", "Donut", "group", {"by": "status"}),
	("Units by Project", "Property Unit", "Bar", "group", {"by": "project"}),
	("Contracts per Month", "Unit Contract", "Bar", "series", {"based_on": "contract_date", "filters": [["Unit Contract", "status", "in", ["Active", "Delivered"]]]}),
	("Maintenance by Category", "Property Maintenance Request", "Donut", "group", {"by": "category"}),
]
GROUPS = [  # (title, icon, collapsed, [(label, kind, target, icon)])
	("Daily Work", None, 0, [
		("Property Unit", "DocType", "Property Unit", "home"), ("Unit Reservation", "DocType", "Unit Reservation", "bookmark"),
		("Unit Contract", "DocType", "Unit Contract", "file-text"), ("Post Dated Cheque", "DocType", "Post Dated Cheque", "banknote"),
		("Unit Handover", "DocType", "Unit Handover", "key"), ("Property Maintenance Request", "DocType", "Property Maintenance Request", "wrench")]),
	("Projects", "building-2", 0, [
		("Real Estate Project", "DocType", "Real Estate Project", "building-2"), ("Project Phase", "DocType", "Project Phase", "flag"),
		("Building", "DocType", "Building", "building"), ("Unit Type", "DocType", "Unit Type", "layout-grid"),
		("Unit Price List", "DocType", "Unit Price List", "tags"), ("Payment Plan", "DocType", "Payment Plan", "calendar")]),
	("Sales Team", "handshake", 0, [
		("Real Estate Broker", "DocType", "Real Estate Broker", "handshake"), ("Sales Commission", "DocType", "Sales Commission", "percent")]),
	("Construction", "hard-hat", 0, [
		("Bill of Quantities", "DocType", "Bill of Quantities", "list-ordered"), ("Construction Contract", "DocType", "Construction Contract", "wrench"),
		("Progress Claim", "DocType", "Progress Claim", "file-check"), ("Construction Progress", "DocType", "Construction Progress", "trending-up")]),
	("After Sale", "key", 0, [
		("Owners Association", "DocType", "Owners Association", "users"), ("Association Fee Run", "DocType", "Association Fee Run", "calculator"),
		("Property Rental Contract", "DocType", "Property Rental Contract", "key-round")]),
	("Reports", "bar-chart-3", 0, [
		("Unit Inventory", "Report", "Unit Inventory", "layout-list"), ("Contracts and Collection", "Report", "Contracts and Collection", "trending-up"),
		("Installments Due", "Report", "Installments Due", "alarm-clock"), ("Collection Forecast", "Report", "Collection Forecast", "calendar-range"),
		("Project Profitability", "Report", "Project Profitability", "scale"), ("Contractor Claims", "Report", "Contractor Claims", "file-text")]),
	("Setup", "settings", 1, [("Real Estate Settings", "DocType", "Real Estate Settings", "settings")]),
	("Related", "link-2", 1, [
		("Customer", "DocType", "Customer", "users"), ("Sales Invoice", "DocType", "Sales Invoice", "receipt"), ("Payment Entry", "DocType", "Payment Entry", "wallet"),
		("Supplier", "DocType", "Supplier", "truck"), ("Purchase Invoice", "DocType", "Purchase Invoice", "receipt"), ("Project", "DocType", "Project", "folder"),
		("Employee", "DocType", "Employee", "user-round")]),
]
TOP = ["Unit Contract", "Unit Reservation", "Installments Due", "Property Unit"]
REPORTS = {"Unit Inventory", "Contracts and Collection", "Installments Due", "Collection Forecast", "Project Profitability", "Contractor Claims"}


def write(path, data):
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w", encoding="utf-8") as fh:
		json.dump(data, fh, indent=1, ensure_ascii=False)
		fh.write("\n")


def slug(n):
	return n.lower().replace(" ", "_").replace("-", "_")


def write_cards():
	for label, dt, flt, fn, _f in CARDS:
		write(os.path.join(BASE, "real_estate", "number_card", slug(label), slug(label) + ".json"), {
			"creation": TS, "docstatus": 0, "doctype": "Number Card", "document_type": dt, "filters_json": json.dumps(flt), "function": fn,
			"idx": 0, "is_public": 1, "is_standard": 1, "label": label, "modified": TS, "modified_by": "Administrator", "module": "Real Estate",
			"name": label, "owner": "Administrator", "show_percentage_stats": 0, "stats_time_interval": "Daily", "type": "Document Type"})
	for name, dt, typ, kind, x in CHARTS:
		d = {"chart_name": name, "creation": TS, "docstatus": 0, "doctype": "Dashboard Chart", "document_type": dt, "dynamic_filters_json": "",
			"idx": 0, "is_public": 1, "is_standard": 1, "modified": TS, "modified_by": "Administrator", "module": "Real Estate", "name": name,
			"number_of_groups": 0, "owner": "Administrator", "type": typ, "use_report_chart": 0, "y_axis": []}
		if kind == "group":
			d.update({"chart_type": "Group By", "group_by_based_on": x["by"], "group_by_type": "Count", "filters_json": "[]", "timeseries": 0})
		else:
			d.update({"chart_type": "Count", "based_on": x["based_on"], "filters_json": json.dumps(x["filters"]), "time_interval": "Monthly",
				"timeseries": 1, "timespan": "Last Year"})
		write(os.path.join(BASE, "real_estate", "dashboard_chart", slug(name), slug(name) + ".json"), d)


def main():
	write_cards()
	rid = lambda: uuid.uuid4().hex[:10]
	content = [{"id": rid(), "type": "header", "data": {"text": '<span class="h4"><b>Real Estate</b></span>', "col": 12}}]
	for label, *_r in CARDS:
		content.append({"id": rid(), "type": "number_card", "data": {"number_card_name": label, "col": 3}})
	for name, *_r in CHARTS:
		content.append({"id": rid(), "type": "chart", "data": {"chart_name": name, "col": 6}})
	shortcuts, links = [], []
	for label in TOP:
		content.insert(1 + len(shortcuts), {"id": rid(), "type": "shortcut", "data": {"shortcut_name": label, "col": 3}})
		kind = "Report" if label in REPORTS else "DocType"
		sc = {"label": label, "link_to": label, "type": kind}
		if kind == "DocType":
			sc["doc_view"] = "List"
		else:
			sc["is_query_report"] = 1
		shortcuts.append(sc)
	for title, _i, _c, items in GROUPS[1:]:
		content.append({"id": rid(), "type": "card", "data": {"card_name": title, "col": 4}})
		links.append({"type": "Card Break", "label": title, "hidden": 0, "is_query_report": 0, "link_count": len(items), "onboard": 0})
		for label, kind, target, _icon in items:
			links.append({"type": "Link", "label": label, "link_type": kind, "link_to": target, "hidden": 0, "is_query_report": 1 if kind == "Report" else 0,
				"onboard": 0, "dependencies": "", "only_for": ""})
	write(os.path.join(BASE, "real_estate", "workspace", "real_estate", "real_estate.json"), {
		"charts": [{"chart_name": c[0], "label": c[0]} for c in CHARTS], "content": json.dumps(content), "creation": TS, "custom_blocks": [], "docstatus": 0, "doctype": "Workspace",
		"for_user": "", "hide_custom": 1, "icon": "building-2", "idx": 1, "is_hidden": 0, "label": "Real Estate", "links": links, "title": "Real Estate", "modified": TS,
		"modified_by": "Administrator", "module": "Real Estate", "name": "Real Estate", "number_cards": [{"label": c[0], "number_card_name": c[0]} for c in CARDS], "owner": "Administrator",
		"parent_page": "", "public": 1, "quick_lists": [], "roles": [], "sequence_id": 24.0, "shortcuts": shortcuts})
	row = lambda i, label, kind, target, icon, child: {"child": child, "collapsible": 1, "doctype": "Sidebar Item", "icon": icon, "idx": i, "indent": 0,
		"keep_closed": 0, "label": label, "link_to": target, "link_type": kind, "parentfield": "items", "parenttype": "Sidebar", "show_arrow": 0, "type": "Link"}
	items = [row(1, "Home", "Workspace", "Real Estate", "house", 0)]
	for title, icon, closed, entries in GROUPS:
		if icon:
			items.append({"child": 0, "collapsible": 1, "doctype": "Sidebar Item", "icon": icon, "idx": len(items) + 1, "indent": 1, "keep_closed": closed,
				"label": title, "link_type": "DocType", "parentfield": "items", "parenttype": "Sidebar", "show_arrow": 0, "type": "Section Break"})
		for label, kind, target, ic in entries:
			items.append(row(len(items) + 1, label, kind, target, ic, 1 if icon else 0))
	write(os.path.join(BASE, "sidebar", "real_estate", "real_estate.json"), {"app": "ledgerx_realestate", "doctype": "Sidebar", "header_icon": "building-2",
		"items": items, "module": "Real Estate", "name": "Real Estate", "standard": 1, "title": "Real Estate"})
	write(os.path.join(BASE, "dock", "real_estate", "real_estate.json"), {"app": "ledgerx_realestate", "creation": TS, "docstatus": 0, "doctype": "Dock", "idx": 0,
		"items": [{"added": 0, "hidden": 0, "icon": "building-2", "link_to": "Real Estate", "link_type": "Sidebar", "title": "Real Estate"}],
		"modified": TS, "modified_by": "Administrator", "name": "real_estate", "owner": "Administrator", "standard": 1})


main()
