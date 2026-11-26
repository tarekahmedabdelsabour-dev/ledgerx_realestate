"""Builds every DocType JSON of ledgerx_realestate from the compact table below.
Run from the repo root:  python3 tools/gen_doctypes.py   (rewrites ledgerx_realestate/education/doctype/*)"""
import json
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..", "ledgerx_realestate", "real_estate", "doctype")
TS = "2026-11-17 20:30:00.000000"
MODULE = "Real Estate"

MGR, SAL, ENG, ACC = "Real Estate Manager", "Real Estate Sales", "Real Estate Engineer", "Real Estate Accountant"


def f(name, ftype, label=None, **kw):
	d = {"fieldname": name, "fieldtype": ftype}
	if ftype not in ("Section Break", "Column Break", "Tab Break"):
		d["label"] = label or name.replace("_", " ").title()
	elif label:
		d["label"] = label
	d.update(kw)
	return d


def sec(name, label=None, **kw):
	return f(name, "Section Break", label, **kw)


def col(name):
	return f(name, "Column Break")


def perms(*rows):
	out = []
	for role, mode in rows:
		p = {"role": role, "read": 1, "report": 1, "print": 1, "export": 1}
		if mode in ("rw", "rwc", "all"):
			p["write"] = 1
		if mode in ("rwc", "all"):
			p["create"] = 1
		if mode == "all":
			p["delete"] = 1
		out.append(p)
	out.append({"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "print": 1, "export": 1})
	return out


DT = {}


def doctype(name, fields, **kw):
	DT[name] = {"name": name, "fields": fields, **kw}


CUR = {"options": "currency"}

ACCT = lambda n, l, **k: f(n, "Link", l, options="Account", **k)



SALES = lambda: perms((MGR, "all"), (SAL, "all"), (ACC, "r"), (ENG, "r"))
PROJ = lambda: perms((MGR, "all"), (SAL, "r"), (ACC, "r"), (ENG, "rw"))
MONEY = lambda: perms((MGR, "all"), (ACC, "all"), (SAL, "r"))
BUILD = lambda: perms((MGR, "all"), (ENG, "all"), (ACC, "r"), (SAL, "r"))
CATS = "Apartment\nVilla\nDuplex\nPenthouse\nStudio\nChalet\nOffice\nShop\nClinic\nLand\nOther"

doctype("Real Estate Settings", [
	f("company", "Link", "Company", options="Company", reqd=1),
	f("vat_rate", "Percent", "VAT on Unit Sales (%)", default=0),
	f("vat_account", "Link", "VAT Account", options="Account"),
	sec("sb_acc", "Accounts"),
	f("sales_income_account", "Link", "Unit Sales Income Account", options="Account"),
	f("deposit_account", "Link", "Maintenance Deposit Account", options="Account", description="A liability: the deposits are held for the owners association."),
	f("late_fee_income_account", "Link", "Late Fee Income Account", options="Account"),
	col("cb1"),
	f("commission_expense_account", "Link", "Commission Expense Account", options="Account"),
	f("construction_cost_account", "Link", "Construction Cost Account", options="Account", description="Contractor claims are posted here (an expense or a work-in-progress asset)."),
	f("retention_account", "Link", "Retention Payable Account", options="Account"),
	f("rental_income_account", "Link", "Rental Income Account", options="Account"),
	f("service_income_account", "Link", "Service Charge Income Account", options="Account"),
	f("maintenance_income_account", "Link", "Maintenance Income Account", options="Account"),
	sec("sb_def", "Defaults"),
	f("reservation_days", "Int", "Reservation Holds the Unit for (days)", default=7),
	f("commission_pct", "Percent", "Default Broker Commission (%)", default=2),
	f("salesman_commission_pct", "Percent", "Salesman Commission (%)", default=0, description="Paid through payroll. 0 switches it off."),
	f("commission_due_pct", "Percent", "Commission Is Due When the Customer Has Paid (%)", default=10),
	col("cb2"),
	f("late_fee_pct", "Percent", "Late Fee per Month (%)", default=0, description="0 switches late fees off."),
	f("grace_days", "Int", "Grace Days Before a Late Fee", default=5),
	f("warranty_months", "Int", "Warranty After Handover (months)", default=12),
	f("handover_needs_payment", "Check", "A Unit Is Handed Over Only When Everything Due Is Paid", default=1),
	f("salary_component", "Data", "Salary Component for Salesmen Commission", default="Real Estate Commission"),
], issingle=1, icon="fa fa-cog", perms=perms((MGR, "rw"), (ACC, "r")))

# ---------------------------------------------------------------- projects and units
doctype("Real Estate Project", [
	f("project_name", "Data", "Project", reqd=1, unique=1, in_list_view=1),
	f("project_type", "Select", "Kind", options="Residential\nCommercial\nAdministrative\nMixed Use\nVillas\nResort\nLand", default="Residential", in_list_view=1),
	f("status", "Select", "Status", options="Planning\nSelling\nUnder Construction\nDelivered\nCompleted", default="Planning", in_list_view=1, in_standard_filter=1),
	f("cost_center", "Link", "Cost Center", options="Cost Center", reqd=1, description="Sales, contractor claims and expenses of the project are posted to it: that is the project's profit and loss."),
	f("erp_project", "Link", "Project (Tasks and Costs)", options="Project", read_only=1, description="Created automatically: attach expenses, tasks and timesheets to it."),
	col("cb1"),
	f("manager", "Link", "Project Manager", options="Employee"),
	f("start_date", "Date", "Start"),
	f("expected_end_date", "Date", "Expected Completion"),
	f("sales_target", "Currency", "Sales Target"),
	sec("sb_loc", "Location"),
	f("city", "Data", "City"),
	f("location", "Data", "Location"),
	f("land_area", "Float", "Land Area (m²)"),
	f("description", "Small Text", "Description"),
], autoname="field:project_name", title_field="project_name", icon="fa fa-building", perms=PROJ())

doctype("Project Phase", [
	f("phase_name", "Data", "Phase", reqd=1, in_list_view=1),
	f("project", "Link", "Project", options="Real Estate Project", reqd=1, in_list_view=1),
	f("status", "Select", "Status", options="Planned\nUnder Construction\nDelivered", default="Planned", in_list_view=1),
	f("start_date", "Date", "Start"),
	f("delivery_date", "Date", "Delivery Date", description="Contracts use it for the delivery payment."),
], autoname="format:{project}-{phase_name}", title_field="phase_name", icon="fa fa-flag", perms=PROJ())

doctype("Building", [
	f("building_name", "Data", "Building", reqd=1, in_list_view=1),
	f("project", "Link", "Project", options="Real Estate Project", reqd=1, in_list_view=1),
	f("phase", "Link", "Phase", options="Project Phase"),
	f("floors", "Int", "Floors"),
	f("status", "Select", "Status", options="Planned\nUnder Construction\nFinished", default="Planned"),
	f("progress_pct", "Percent", "Completion", read_only=1, description="From the latest construction progress record."),
], autoname="format:{project}-{building_name}", title_field="building_name", icon="fa fa-building-o", perms=PROJ())

doctype("Unit Type", [
	f("type_name", "Data", "Unit Type", reqd=1, unique=1, in_list_view=1, description="For example: Apartment 3 bedrooms 150 m²."),
	f("category", "Select", "Category", options=CATS, default="Apartment", reqd=1, in_list_view=1),
	f("area_built", "Float", "Built Area (m²)", in_list_view=1),
	f("area_garden", "Float", "Garden or Roof Area (m²)"),
	f("bedrooms", "Int", "Bedrooms"),
	f("bathrooms", "Int", "Bathrooms"),
	f("description", "Small Text", "Description"),
], autoname="field:type_name", icon="fa fa-th-large", perms=PROJ())

doctype("Property Unit", [
	f("unit_number", "Data", "Unit Number", reqd=1, in_list_view=1),
	f("project", "Link", "Project", options="Real Estate Project", reqd=1, in_list_view=1, in_standard_filter=1),
	f("status", "Select", "Status", options="Available\nReserved\nContracted\nDelivered\nBlocked\nRented", default="Available", read_only=1, in_list_view=1, in_standard_filter=1),
	f("phase", "Link", "Phase", options="Project Phase"),
	f("building", "Link", "Building", options="Building"),
	f("floor", "Int", "Floor"),
	col("cb1"),
	f("unit_type", "Link", "Unit Type", options="Unit Type"),
	f("category", "Select", "Category", options=CATS, default="Apartment", in_list_view=1, in_standard_filter=1),
	f("finishing", "Select", "Finishing", options="\nCore and Shell\nSemi Finished\nFully Finished"),
	f("view", "Data", "View"),
	sec("sb_area", "Area and Rooms"),
	f("area_built", "Float", "Built Area (m²)", in_list_view=1),
	f("area_garden", "Float", "Garden or Roof Area (m²)"),
	f("bedrooms", "Int", "Bedrooms"),
	col("cb2"),
	f("bathrooms", "Int", "Bathrooms"),
	sec("sb_price", "Price"),
	f("premium_pct", "Percent", "Floor, View or Corner Premium (%)", description="Added on top of the price list."),
	f("list_price", "Currency", "Price", in_list_view=1),
	col("cb3"),
	f("cost_estimate", "Currency", "Estimated Cost"),
	sec("sb_sale", "Sale"),
	f("contract", "Link", "Contract", options="Unit Contract", read_only=1),
	f("owner_customer", "Link", "Owner", options="Customer", read_only=1),
	col("cb4"),
	f("warranty_end", "Date", "Warranty Ends", read_only=1),
	f("notes", "Small Text", "Notes"),
], autoname="format:{project}-{unit_number}", title_field="unit_number", icon="fa fa-home", search_fields="unit_number,project,building", perms=PROJ())

doctype("Unit Price Row", [
	f("unit_type", "Link", "Unit Type", options="Unit Type", reqd=1, in_list_view=1),
	f("per_m2", "Currency", "Price per m² (built)", reqd=1, in_list_view=1),
	f("garden_per_m2", "Currency", "Price per m² (garden or roof)", in_list_view=1),
], istable=1)

doctype("Unit Price List", [
	f("title", "Data", "Name", reqd=1, in_list_view=1),
	f("project", "Link", "Project", options="Real Estate Project", reqd=1, in_list_view=1),
	f("effective_from", "Date", "Effective From", default="Today", reqd=1),
	f("active", "Check", "Active", default=1),
	sec("sb_rows", "Prices"),
	f("rows", "Table", "Prices by Unit Type", options="Unit Price Row", reqd=1),
], autoname="format:{project}-{title}", title_field="title", icon="fa fa-tags", perms=MONEY())

doctype("Payment Plan Extra", [
	f("months", "Int", "After (months from the contract)", reqd=1, in_list_view=1),
	f("percent", "Percent", "Share (%)", reqd=1, in_list_view=1),
], istable=1)

doctype("Payment Plan", [
	f("plan_name", "Data", "Plan", reqd=1, unique=1, in_list_view=1, description="For example: 10% down, 8 years quarterly, 5% at delivery."),
	f("project", "Link", "Project", options="Real Estate Project", description="Empty: usable in every project."),
	f("active", "Check", "Active", default=1),
	col("cb1"),
	f("down_payment_pct", "Percent", "Down Payment (%)", default=10, in_list_view=1),
	f("delivery_pct", "Percent", "Paid at Delivery (%)", default=0),
	f("markup_pct", "Percent", "Price Increase for This Plan (%)", default=0, in_list_view=1),
	sec("sb_inst", "Installments"),
	f("installments", "Int", "Number of Installments", default=1, in_list_view=1),
	f("interval_months", "Int", "Months Between Installments", default=3, in_list_view=1),
	f("first_after_months", "Int", "First Installment After (months)", default=3),
	col("cb2"),
	f("maintenance_deposit_pct", "Percent", "Maintenance Deposit (%)", default=0, description="Added to the contract, due at delivery, held for the owners association."),
	sec("sb_ext", "Extra Payments"),
	f("extras", "Table", "Extra Payments (for example yearly)", options="Payment Plan Extra"),
], autoname="field:plan_name", icon="fa fa-calendar", perms=MONEY())

doctype("Real Estate Broker", [
	f("broker_name", "Data", "Broker or Company", reqd=1, in_list_view=1),
	f("broker_type", "Select", "Kind", options="Individual\nCompany", default="Individual"),
	f("phone", "Data", "Phone", in_list_view=1),
	f("email", "Data", "Email", options="Email"),
	col("cb1"),
	f("tax_id", "Data", "National or Tax ID"),
	f("commission_pct", "Percent", "Commission (%)", in_list_view=1),
	f("active", "Check", "Active", default=1),
	f("supplier", "Link", "Supplier (Payable Account)", options="Supplier", read_only=1, description="Created automatically: commissions are paid through it."),
], autoname="field:broker_name", icon="fa fa-handshake-o", perms=SALES())

doctype("Unit Reservation", [
	f("unit", "Link", "Unit", options="Property Unit", reqd=1, in_list_view=1),
	f("customer", "Link", "Customer", options="Customer", reqd=1, in_list_view=1),
	f("status", "Select", "Status", options="Active\nConverted\nCancelled\nExpired", default="Active", read_only=1, in_list_view=1),
	f("valid_until", "Date", "Holds the Unit Until", reqd=1),
	col("cb1"),
	f("deposit", "Currency", "Deposit", in_list_view=1),
	f("deposit_entry", "Link", "Payment Entry", options="Payment Entry", read_only=1),
	f("broker", "Link", "Broker", options="Real Estate Broker"),
	f("salesman", "Link", "Salesman", options="Employee"),
	f("crm_lead", "Data", "CRM Lead"),
	f("contract", "Link", "Contract", options="Unit Contract", read_only=1),
	f("notes", "Small Text", "Notes"),
], autoname="naming_series:", icon="fa fa-bookmark", perms=SALES())
DT["Unit Reservation"]["fields"].insert(0, f("naming_series", "Select", "Series", options="RES-.YYYY.-.#####", default="RES-.YYYY.-.#####", hidden=1))

doctype("Contract Installment", [
	f("due_date", "Date", "Due Date", reqd=1, in_list_view=1),
	f("label", "Data", "Kind", in_list_view=1),
	f("amount", "Currency", "Amount", reqd=1, in_list_view=1),
], istable=1)

doctype("Contract Late Fee", [
	f("fee_date", "Date", "Date", in_list_view=1),
	f("base", "Currency", "Overdue Amount", in_list_view=1),
	f("fee", "Currency", "Late Fee", in_list_view=1),
	f("sales_invoice", "Link", "Invoice", options="Sales Invoice", in_list_view=1),
], istable=1)

doctype("Unit Contract", [
	f("unit", "Link", "Unit", options="Property Unit", reqd=1, in_list_view=1),
	f("customer", "Link", "Customer", options="Customer", reqd=1, in_list_view=1),
	f("status", "Select", "Status", options="Draft\nActive\nDelivered\nCancelled", default="Draft", read_only=1, in_list_view=1, in_standard_filter=1),
	f("contract_date", "Date", "Contract Date", default="Today", reqd=1),
	f("project", "Link", "Project", options="Real Estate Project", fetch_from="unit.project", read_only=1, in_standard_filter=1),
	col("cb1"),
	f("reservation", "Link", "Reservation", options="Unit Reservation"),
	f("salesman", "Link", "Salesman", options="Employee"),
	f("broker", "Link", "Broker", options="Real Estate Broker"),
	f("commission_pct", "Percent", "Broker Commission (%)"),
	sec("sb_price", "Price"),
	f("list_price", "Currency", "List Price", read_only=1),
	f("discount", "Currency", "Discount"),
	col("cb2"),
	f("payment_plan", "Link", "Payment Plan", options="Payment Plan", reqd=1),
	f("delivery_date", "Date", "Delivery Date"),
	sec("sb_plan", "Plan Terms"),
	f("down_payment_pct", "Percent", "Down Payment (%)"),
	f("delivery_pct", "Percent", "Paid at Delivery (%)"),
	f("markup_pct", "Percent", "Price Increase (%)"),
	f("deposit_pct", "Percent", "Maintenance Deposit (%)"),
	col("cb3"),
	f("installments", "Int", "Number of Installments"),
	f("interval_months", "Int", "Months Between Installments"),
	f("first_after_months", "Int", "First Installment After (months)"),
	f("extras", "Table", "Extra Payments", options="Payment Plan Extra"),
	sec("sb_tot", "Totals"),
	f("net", "Currency", "After Discount", read_only=1),
	f("markup", "Currency", "Plan Increase", read_only=1),
	f("price", "Currency", "Contract Price", read_only=1, in_list_view=1),
	col("cb4"),
	f("deposit", "Currency", "Maintenance Deposit", read_only=1),
	f("vat", "Currency", "VAT", read_only=1),
	f("total", "Currency", "Invoice Total", read_only=1),
	sec("sb_sched", "Payment Schedule"),
	f("schedule", "Table", "Schedule", options="Contract Installment", read_only=1),
	f("schedule_html", "HTML", "Collection"),
	sec("sb_acc", "Accounting"),
	f("sales_invoice", "Link", "Sales Invoice", options="Sales Invoice", read_only=1, no_copy=1),
	f("return_invoice", "Link", "Credit Note (Cancellation)", options="Sales Invoice", read_only=1, no_copy=1),
	col("cb5"),
	f("late_fees", "Table", "Late Fees Charged", options="Contract Late Fee", read_only=1),
], autoname="naming_series:", title_field="customer", icon="fa fa-file-text", search_fields="customer,unit", perms=SALES())
DT["Unit Contract"]["fields"].insert(0, f("naming_series", "Select", "Series", options="CON-.YYYY.-.#####", default="CON-.YYYY.-.#####", hidden=1))

doctype("Post Dated Cheque", [
	f("contract", "Link", "Contract", options="Unit Contract", reqd=1, in_list_view=1),
	f("customer", "Link", "Customer", options="Customer", fetch_from="contract.customer", read_only=1, in_list_view=1),
	f("cheque_number", "Data", "Cheque Number", reqd=1, in_list_view=1),
	f("bank", "Data", "Bank", in_list_view=1),
	col("cb1"),
	f("due_date", "Date", "Cheque Date", reqd=1, in_list_view=1),
	f("amount", "Currency", "Amount", reqd=1, in_list_view=1),
	f("status", "Select", "Status", options="Received\nDeposited\nCleared\nBounced\nReturned", default="Received", read_only=1, in_list_view=1, in_standard_filter=1),
	f("payment_entry", "Link", "Payment Entry", options="Payment Entry", read_only=1),
	f("notes", "Small Text", "Notes"),
], autoname="hash", title_field="cheque_number", icon="fa fa-money", perms=MONEY())

doctype("Sales Commission", [
	f("contract", "Link", "Contract", options="Unit Contract", reqd=1, in_list_view=1),
	f("party_type", "Select", "Paid To", options="Broker\nEmployee", default="Broker", reqd=1, in_list_view=1),
	f("broker", "Link", "Broker", options="Real Estate Broker", depends_on="eval:doc.party_type=='Broker'"),
	f("employee", "Link", "Salesman", options="Employee", depends_on="eval:doc.party_type=='Employee'"),
	f("status", "Select", "Status", options="Pending\nDue\nInvoiced\nCancelled", default="Pending", read_only=1, in_list_view=1, in_standard_filter=1),
	col("cb1"),
	f("base_amount", "Currency", "Contract Price"),
	f("pct", "Percent", "Commission (%)"),
	f("amount", "Currency", "Commission", in_list_view=1),
	f("purchase_invoice", "Link", "Purchase Invoice", options="Purchase Invoice", read_only=1),
	f("additional_salary", "Link", "Additional Salary", options="Additional Salary", read_only=1),
], autoname="hash", icon="fa fa-percent", perms=MONEY())

# ---------------------------------------------------------------- construction
doctype("BOQ Item", [
	f("description", "Data", "Work Item", reqd=1, in_list_view=1),
	f("uom", "Data", "Unit", in_list_view=1),
	f("quantity", "Float", "Quantity", reqd=1, in_list_view=1),
	f("rate", "Currency", "Rate", reqd=1, in_list_view=1),
	f("amount", "Currency", "Amount", read_only=1, in_list_view=1),
], istable=1)

doctype("Bill of Quantities", [
	f("title", "Data", "Title", reqd=1, in_list_view=1),
	f("project", "Link", "Project", options="Real Estate Project", reqd=1, in_list_view=1),
	f("phase", "Link", "Phase", options="Project Phase"),
	f("building", "Link", "Building", options="Building"),
	f("status", "Select", "Status", options="Draft\nApproved", default="Draft", in_list_view=1),
	col("cb1"),
	f("total_budget", "Currency", "Total Budget", read_only=1, in_list_view=1),
	sec("sb_items", "Work Items"),
	f("items", "Table", "Work Items", options="BOQ Item", reqd=1),
], autoname="hash", title_field="title", icon="fa fa-list-ol", perms=BUILD())

doctype("Construction Contract", [
	f("title", "Data", "Title", reqd=1, in_list_view=1),
	f("project", "Link", "Project", options="Real Estate Project", reqd=1, in_list_view=1),
	f("contractor", "Link", "Contractor", options="Supplier", reqd=1, in_list_view=1),
	f("status", "Select", "Status", options="Draft\nActive\nCompleted\nCancelled", default="Draft", read_only=1, in_list_view=1),
	f("boq", "Link", "Bill of Quantities", options="Bill of Quantities"),
	col("cb1"),
	f("contract_value", "Currency", "Contract Value", reqd=1, in_list_view=1),
	f("retention_pct", "Percent", "Retention (%)", default=5),
	f("advance_pct", "Percent", "Advance Recovered from Each Claim (%)", default=0),
	f("start_date", "Date", "Start"),
	f("end_date", "Date", "End"),
	sec("sb_prog", "Progress"),
	f("advance_paid", "Currency", "Advance Paid", read_only=1),
	f("claimed_gross", "Currency", "Claimed to Date", read_only=1),
	f("last_pct", "Percent", "Completion Claimed", read_only=1),
	f("scope", "Small Text", "Scope of Work"),
], autoname="naming_series:", title_field="title", icon="fa fa-wrench", perms=BUILD())
DT["Construction Contract"]["fields"].insert(0, f("naming_series", "Select", "Series", options="CC-.YYYY.-.####", default="CC-.YYYY.-.####", hidden=1))

doctype("Progress Claim", [
	f("construction_contract", "Link", "Construction Contract", options="Construction Contract", reqd=1, in_list_view=1),
	f("project", "Link", "Project", options="Real Estate Project", fetch_from="construction_contract.project", read_only=1),
	f("contractor", "Link", "Contractor", options="Supplier", fetch_from="construction_contract.contractor", read_only=1, in_list_view=1),
	f("claim_date", "Date", "Date", default="Today", reqd=1),
	f("status", "Select", "Status", options="Draft\nApproved\nCancelled", default="Draft", read_only=1, in_list_view=1),
	col("cb1"),
	f("cumulative_pct", "Percent", "Total Completion to Date (%)", reqd=1, in_list_view=1),
	f("penalties", "Currency", "Penalties"),
	f("notes", "Small Text", "Notes"),
	sec("sb_calc", "Calculation"),
	f("contract_value", "Currency", "Contract Value", read_only=1),
	f("cumulative_value", "Currency", "Work Done to Date", read_only=1),
	f("previous_gross", "Currency", "Claimed Before", read_only=1),
	col("cb2"),
	f("gross", "Currency", "This Claim", read_only=1),
	f("retention", "Currency", "Retention", read_only=1),
	f("advance_recovery", "Currency", "Advance Recovered", read_only=1),
	f("net", "Currency", "Net Payable", read_only=1, in_list_view=1),
	sec("sb_acc", "Accounting"),
	f("purchase_invoice", "Link", "Purchase Invoice", options="Purchase Invoice", read_only=1, no_copy=1),
], autoname="naming_series:", icon="fa fa-file-text-o", perms=BUILD())
DT["Progress Claim"]["fields"].insert(0, f("naming_series", "Select", "Series", options="PCL-.YYYY.-.#####", default="PCL-.YYYY.-.#####", hidden=1))

doctype("Construction Progress", [
	f("project", "Link", "Project", options="Real Estate Project", reqd=1, in_list_view=1),
	f("building", "Link", "Building", options="Building", in_list_view=1),
	f("progress_date", "Date", "Date", default="Today", reqd=1, in_list_view=1),
	f("completion_pct", "Percent", "Completion (%)", reqd=1, in_list_view=1),
	col("cb1"),
	f("photo", "Attach Image", "Photo"),
	f("notes", "Small Text", "Notes"),
], autoname="hash", title_field="project", icon="fa fa-line-chart", perms=BUILD())

# ---------------------------------------------------------------- after the sale
doctype("Handover Check", [
	f("item", "Data", "Item", reqd=1, in_list_view=1),
	f("ok", "Check", "Accepted", in_list_view=1),
	f("notes", "Data", "Notes", in_list_view=1),
], istable=1)

doctype("Handover Defect", [
	f("description", "Data", "Defect", reqd=1, in_list_view=1),
	f("severity", "Select", "Severity", options="Minor\nMajor", default="Minor", in_list_view=1),
	f("fixed", "Check", "Fixed", in_list_view=1),
], istable=1)

doctype("Unit Handover", [
	f("contract", "Link", "Contract", options="Unit Contract", reqd=1, in_list_view=1),
	f("unit", "Link", "Unit", options="Property Unit", fetch_from="contract.unit", read_only=1, in_list_view=1),
	f("customer", "Link", "Customer", options="Customer", fetch_from="contract.customer", read_only=1, in_list_view=1),
	f("status", "Select", "Status", options="Scheduled\nCompleted\nCancelled", default="Scheduled", read_only=1, in_list_view=1),
	col("cb1"),
	f("handover_date", "Date", "Handover Date", default="Today", reqd=1),
	f("received_by", "Data", "Received By"),
	f("keys", "Int", "Keys Handed Over"),
	f("electricity_reading", "Float", "Electricity Meter"),
	f("water_reading", "Float", "Water Meter"),
	f("warranty_months", "Int", "Warranty (months)"),
	f("warranty_end", "Date", "Warranty Ends", read_only=1),
	sec("sb_chk", "Checklist"),
	f("checklist", "Table", "Checklist", options="Handover Check"),
	sec("sb_def", "Defects"),
	f("defects", "Table", "Defects", options="Handover Defect"),
], autoname="naming_series:", icon="fa fa-key", perms=perms((MGR, "all"), (ENG, "all"), (SAL, "rw"), (ACC, "r")))
DT["Unit Handover"]["fields"].insert(0, f("naming_series", "Select", "Series", options="HND-.YYYY.-.#####", default="HND-.YYYY.-.#####", hidden=1))

doctype("Property Maintenance Request", [
	f("unit", "Link", "Unit", options="Property Unit", reqd=1, in_list_view=1),
	f("customer", "Link", "Customer", options="Customer", in_list_view=1),
	f("category", "Select", "Category", options="Plumbing\nElectrical\nFinishing\nAir Conditioning\nStructural\nElevator\nOther", default="Other", reqd=1, in_list_view=1),
	f("priority", "Select", "Priority", options="Low\nNormal\nHigh\nEmergency", default="Normal"),
	f("status", "Select", "Status", options="New\nAssigned\nIn Progress\nDone\nClosed", default="New", in_list_view=1, in_standard_filter=1),
	col("cb1"),
	f("reported_on", "Date", "Reported On", default="Today"),
	f("under_warranty", "Check", "Under Warranty", read_only=1),
	f("assigned_employee", "Link", "Assigned To", options="Employee"),
	f("assigned_supplier", "Link", "Contractor", options="Supplier"),
	sec("sb_d", "Details"),
	f("description", "Small Text", "Problem", reqd=1),
	f("resolution", "Small Text", "What Was Done"),
	sec("sb_c", "Cost"),
	f("cost", "Currency", "Our Cost"),
	f("charge", "Currency", "Charged to the Owner", description="Not charged while under warranty unless you enter it."),
	f("sales_invoice", "Link", "Invoice", options="Sales Invoice", read_only=1),
], autoname="naming_series:", icon="fa fa-wrench", perms=BUILD())
DT["Property Maintenance Request"]["fields"].insert(0, f("naming_series", "Select", "Series", options="MNT-.YYYY.-.#####", default="MNT-.YYYY.-.#####", hidden=1))

doctype("Owners Association", [
	f("association_name", "Data", "Association", reqd=1, unique=1, in_list_view=1),
	f("project", "Link", "Project", options="Real Estate Project", reqd=1, in_list_view=1),
	f("building", "Link", "Building", options="Building", description="Empty: the whole project."),
	f("active", "Check", "Active", default=1),
	col("cb1"),
	f("rate_per_m2", "Currency", "Monthly Charge per m²", in_list_view=1),
	f("fixed_fee", "Currency", "Fixed Monthly Charge per Unit"),
	f("notes", "Small Text", "Notes"),
], autoname="field:association_name", icon="fa fa-users", perms=MONEY())

doctype("Fee Run Line", [
	f("unit", "Link", "Unit", options="Property Unit", in_list_view=1),
	f("customer", "Link", "Owner", options="Customer", in_list_view=1),
	f("amount", "Currency", "Amount", in_list_view=1),
	f("sales_invoice", "Link", "Invoice", options="Sales Invoice", in_list_view=1),
], istable=1)

doctype("Association Fee Run", [
	f("association", "Link", "Association", options="Owners Association", reqd=1, in_list_view=1),
	f("period", "Data", "Period", reqd=1, in_list_view=1, description="For example 2026-12."),
	f("posting_date", "Date", "Invoice Date", default="Today", reqd=1),
	f("status", "Select", "Status", options="Draft\nPosted", default="Draft", read_only=1, in_list_view=1),
	col("cb1"),
	f("invoices_count", "Int", "Invoices", read_only=1),
	f("total", "Currency", "Total", read_only=1),
	sec("sb_l", "Charges"),
	f("lines", "Table", "Charges", options="Fee Run Line", read_only=1),
], autoname="naming_series:", icon="fa fa-calculator", perms=MONEY())
DT["Association Fee Run"]["fields"].insert(0, f("naming_series", "Select", "Series", options="AFR-.YYYY.-.###", default="AFR-.YYYY.-.###", hidden=1))

doctype("Rental Invoice", [
	f("period_start", "Date", "Month", in_list_view=1),
	f("amount", "Currency", "Rent", in_list_view=1),
	f("sales_invoice", "Link", "Invoice", options="Sales Invoice", in_list_view=1),
], istable=1)

doctype("Property Rental Contract", [
	f("unit", "Link", "Unit", options="Property Unit", reqd=1, in_list_view=1),
	f("tenant", "Link", "Tenant", options="Customer", reqd=1, in_list_view=1),
	f("status", "Select", "Status", options="Draft\nActive\nEnded\nCancelled", default="Draft", read_only=1, in_list_view=1, in_standard_filter=1),
	col("cb1"),
	f("start_date", "Date", "Start", reqd=1),
	f("end_date", "Date", "End", reqd=1),
	f("monthly_rent", "Currency", "Monthly Rent", reqd=1, in_list_view=1),
	f("annual_increase_pct", "Percent", "Yearly Increase (%)"),
	sec("sb_dep", "Security Deposit"),
	f("security_deposit", "Currency", "Security Deposit"),
	f("deposit_entry", "Link", "Payment Entry", options="Payment Entry", read_only=1),
	col("cb2"),
	f("last_billed", "Date", "Billed Up To", read_only=1),
	sec("sb_inv", "Rent Invoices"),
	f("invoices", "Table", "Invoices", options="Rental Invoice", read_only=1),
], autoname="naming_series:", title_field="tenant", icon="fa fa-key", perms=SALES())
DT["Property Rental Contract"]["fields"].insert(0, f("naming_series", "Select", "Series", options="RNT-.YYYY.-.####", default="RNT-.YYYY.-.####", hidden=1))

def build():
	os.makedirs(ROOT, exist_ok=True)
	for name, d in DT.items():
		fields = d["fields"]
		order = [x["fieldname"] for x in fields]
		istable = d.get("istable", 0)
		out = {
			"actions": [], "creation": TS, "doctype": "DocType", "engine": "InnoDB", "field_order": order, "fields": fields,
			"links": [], "modified": TS, "modified_by": "Administrator", "module": MODULE, "name": name, "owner": "Administrator",
			"sort_field": "creation", "sort_order": "DESC", "states": [],
			"permissions": [] if istable else d.get("perms", []),
		}
		for k in ("autoname", "title_field", "icon", "track_changes", "issingle", "istable", "show_title_field_in_link", "search_fields"):
			if k in d:
				out[k] = d[k]
		if not istable and "track_changes" not in d and name not in ("Room Night Lock", "Production Scan", "Class Attendance"):
			out["track_changes"] = 1  # who changed what, when
		if "autoname" not in d and not istable and not d.get("issingle"):
			out["autoname"] = "hash"
		out["allow_rename"] = 0
		slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
		folder = os.path.join(ROOT, slug)
		os.makedirs(folder, exist_ok=True)
		open(os.path.join(folder, "__init__.py"), "a").close()
		with open(os.path.join(folder, slug + ".json"), "w", encoding="utf-8") as fh:
			json.dump(out, fh, indent=1, ensure_ascii=False)
			fh.write("\n")
		py = os.path.join(folder, slug + ".py")
		if not os.path.exists(py):
			cls = "".join(w.capitalize() for w in re.split(r"[^A-Za-z0-9]+", name))
			with open(py, "w") as fh:
				fh.write(f"from frappe.model.document import Document\n\n\nclass {cls}(Document):\n\tpass\n")


if __name__ == "__main__":
	build()
	print(len(DT), "doctypes")
