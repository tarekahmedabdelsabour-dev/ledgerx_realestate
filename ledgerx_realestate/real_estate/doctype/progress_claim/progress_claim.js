(() => {
	const act = (frm, method, args) => frm.call({ doc: frm.doc, method, args: args || {}, freeze: true }).then((r) => { frm.reload_doc(); return r; });
	const ask = (frm, title, fields, method) => {
		const d = new frappe.ui.Dialog({ title, fields, primary_action_label: __("Save"), primary_action(v) { d.hide(); act(frm, method, v); } });
		d.show();
	};
	const MOP = { fieldname: "mode_of_payment", fieldtype: "Link", options: "Mode of Payment", label: __("Mode of Payment"), reqd: 1 };
	frappe.ui.form.on("Progress Claim", {
		refresh(frm) {
			if (frm.is_new()) return;
			if (frm.doc.status === "Draft") {
				frm.add_custom_button(__("Approve and Post"), () => frappe.confirm(__("Create the purchase invoice for this claim?"), () => act(frm, "approve"))).addClass("btn-primary");
				frm.add_custom_button(__("Cancel Draft"), () => act(frm, "cancel_draft"), __("More"));
			}
			if (frm.doc.purchase_invoice) frm.add_custom_button(__("Open Invoice"), () => frappe.set_route("Form", "Purchase Invoice", frm.doc.purchase_invoice));
		},
	});
})();
