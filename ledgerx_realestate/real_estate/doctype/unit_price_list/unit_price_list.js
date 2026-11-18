(() => {
	const act = (frm, method, args) => frm.call({ doc: frm.doc, method, args: args || {}, freeze: true }).then((r) => { frm.reload_doc(); return r; });
	const ask = (frm, title, fields, method) => {
		const d = new frappe.ui.Dialog({ title, fields, primary_action_label: __("Save"), primary_action(v) { d.hide(); act(frm, method, v); } });
		d.show();
	};
	const MOP = { fieldname: "mode_of_payment", fieldtype: "Link", options: "Mode of Payment", label: __("Mode of Payment"), reqd: 1 };
	frappe.ui.form.on("Unit Price List", {
		refresh(frm) {
			if (frm.is_new()) return;
			frm.add_custom_button(__("Apply to Available Units"), () => frappe.confirm(__("Set the price of every available unit of the project from this list?"),
				() => frm.call({ doc: frm.doc, method: "apply", freeze: true }).then((r) => frappe.show_alert({ message: __("{0} units priced", [r.message]), indicator: "green" }))));
		},
	});
})();
