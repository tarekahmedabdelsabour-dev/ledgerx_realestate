(() => {
	const act = (frm, method, args) => frm.call({ doc: frm.doc, method, args: args || {}, freeze: true }).then((r) => { frm.reload_doc(); return r; });
	const ask = (frm, title, fields, method) => {
		const d = new frappe.ui.Dialog({ title, fields, primary_action_label: __("Save"), primary_action(v) { d.hide(); act(frm, method, v); } });
		d.show();
	};
	const MOP = { fieldname: "mode_of_payment", fieldtype: "Link", options: "Mode of Payment", label: __("Mode of Payment"), reqd: 1 };
	frappe.ui.form.on("Property Unit", {
		setup(frm) { frm.set_query("building", () => ({ filters: { project: frm.doc.project } })); frm.set_query("phase", () => ({ filters: { project: frm.doc.project } })); },
		unit_type(frm) {
			if (!frm.doc.unit_type) return;
			frappe.db.get_doc("Unit Type", frm.doc.unit_type).then((t) => frm.set_value({ category: t.category, area_built: frm.doc.area_built || t.area_built,
				area_garden: frm.doc.area_garden || t.area_garden, bedrooms: frm.doc.bedrooms || t.bedrooms, bathrooms: frm.doc.bathrooms || t.bathrooms }));
		},
		refresh(frm) {
			if (frm.is_new()) return;
			if (frm.doc.status === "Available") {
				frm.add_custom_button(__("Reserve"), () => frappe.new_doc("Unit Reservation", { unit: frm.doc.name }), __("Sell"));
				frm.add_custom_button(__("Contract"), () => frappe.new_doc("Unit Contract", { unit: frm.doc.name }), __("Sell"));
				frm.add_custom_button(__("Rent"), () => frappe.new_doc("Property Rental Contract", { unit: frm.doc.name }), __("Sell"));
				frm.add_custom_button(__("Take Off Sale"), () => act(frm, "set_blocked", { blocked: 1 }), __("More"));
			}
			if (frm.doc.status === "Blocked") frm.add_custom_button(__("Put Back on Sale"), () => act(frm, "set_blocked", { blocked: 0 }));
			if (frm.doc.contract) frm.add_custom_button(__("Open Contract"), () => frappe.set_route("Form", "Unit Contract", frm.doc.contract));
			if (["Delivered", "Rented"].includes(frm.doc.status)) frm.add_custom_button(__("Property Maintenance Request"), () => frappe.new_doc("Property Maintenance Request", { unit: frm.doc.name }), __("Create"));
		},
	});
})();
