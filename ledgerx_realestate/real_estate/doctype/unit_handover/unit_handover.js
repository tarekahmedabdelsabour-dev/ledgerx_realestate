(() => {
	const act = (frm, method, args) => frm.call({ doc: frm.doc, method, args: args || {}, freeze: true }).then((r) => { frm.reload_doc(); return r; });
	const ask = (frm, title, fields, method) => {
		const d = new frappe.ui.Dialog({ title, fields, primary_action_label: __("Save"), primary_action(v) { d.hide(); act(frm, method, v); } });
		d.show();
	};
	const MOP = { fieldname: "mode_of_payment", fieldtype: "Link", options: "Mode of Payment", label: __("Mode of Payment"), reqd: 1 };
	frappe.ui.form.on("Unit Handover", {
		setup(frm) { frm.set_query("contract", () => ({ filters: { status: "Active" } })); },
		refresh(frm) {
			if (frm.is_new() || frm.doc.status !== "Scheduled") return;
			frm.add_custom_button(__("Complete the Handover"), () => frappe.confirm(__("Hand the unit over to the owner? The warranty starts today."), () => act(frm, "complete"))).addClass("btn-primary");
			frm.add_custom_button(__("Cancel"), () => act(frm, "cancel_handover"), __("More"));
		},
	});
})();
