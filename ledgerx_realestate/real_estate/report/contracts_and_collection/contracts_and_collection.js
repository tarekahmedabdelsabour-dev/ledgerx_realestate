frappe.query_reports["Contracts and Collection"] = {
	filters: [
		{ fieldname: "from_date", label: __("From"), fieldtype: "Date", default: frappe.datetime.add_days(frappe.datetime.get_today(), -364) },
		{ fieldname: "to_date", label: __("To"), fieldtype: "Date", default: frappe.datetime.get_today() },
		{ fieldname: "project", label: __("Project"), fieldtype: "Link", options: "Real Estate Project" },
		{ fieldname: "broker", label: __("Broker"), fieldtype: "Link", options: "Real Estate Broker" },
		{ fieldname: "salesman", label: __("Salesman"), fieldtype: "Link", options: "Employee" },
	],
};
