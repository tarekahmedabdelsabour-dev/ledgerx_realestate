frappe.query_reports["Collection Forecast"] = {
	filters: [
		{ fieldname: "from_date", label: __("From"), fieldtype: "Date", default: frappe.datetime.get_today() },
		{ fieldname: "to_date", label: __("To"), fieldtype: "Date", default: frappe.datetime.add_months(frappe.datetime.get_today(), 12) },
		{ fieldname: "project", label: __("Project"), fieldtype: "Link", options: "Real Estate Project" },
	],
};
