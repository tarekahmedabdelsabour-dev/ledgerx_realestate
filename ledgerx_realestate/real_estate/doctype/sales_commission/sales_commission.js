(() => {
	const act = (frm, method, args) => frm.call({ doc: frm.doc, method, args: args || {}, freeze: true }).then((r) => { frm.reload_doc(); return r; });
	const ask = (frm, title, fields, method) => {
		const d = new frappe.ui.Dialog({ title, fields, primary_action_label: __("Save"), primary_action(v) { d.hide(); act(frm, method, v); } });
		d.show();
	};
	const MOP = { fieldname: "mode_of_payment", fieldtype: "Link", options: "Mode of Payment", label: __("Mode of Payment"), reqd: 1 };
	frappe.ui.form.on("Sales Commission", {
		refresh(frm) {
			if (!frm.is_new() && ["Pending", "Due"].includes(frm.doc.status))
				frm.add_custom_button(__("Pay the Commission"), () => frappe.confirm(__("Create the purchase invoice or the additional salary?"), () => act(frm, "pay"))).addClass("btn-primary");
		},
	});
})();
