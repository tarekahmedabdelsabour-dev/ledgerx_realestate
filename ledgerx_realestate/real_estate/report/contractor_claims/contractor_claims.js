frappe.query_reports["Contractor Claims"] = {
	filters: [
		{ fieldname: "project", label: __("Project"), fieldtype: "Link", options: "Real Estate Project" },
		{ fieldname: "contractor", label: __("Contractor"), fieldtype: "Link", options: "Supplier" },
	],
};
