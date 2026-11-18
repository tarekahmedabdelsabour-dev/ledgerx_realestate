frappe.query_reports["Unit Inventory"] = {
	filters: [
		{ fieldname: "project", label: __("Project"), fieldtype: "Link", options: "Real Estate Project" },
		{ fieldname: "building", label: __("Building"), fieldtype: "Link", options: "Building" },
		{ fieldname: "status", label: __("Status"), fieldtype: "Select", options: "\nAvailable\nReserved\nContracted\nDelivered\nBlocked\nRented" },
		{ fieldname: "category", label: __("Category"), fieldtype: "Select", options: "\nApartment\nVilla\nDuplex\nPenthouse\nStudio\nChalet\nOffice\nShop\nClinic\nLand\nOther" },
	],
};
