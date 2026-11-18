(() => {
	const act = (frm, method, args) => frm.call({ doc: frm.doc, method, args: args || {}, freeze: true }).then((r) => { frm.reload_doc(); return r; });
	const ask = (frm, title, fields, method) => {
		const d = new frappe.ui.Dialog({ title, fields, primary_action_label: __("Save"), primary_action(v) { d.hide(); act(frm, method, v); } });
		d.show();
	};
	const MOP = { fieldname: "mode_of_payment", fieldtype: "Link", options: "Mode of Payment", label: __("Mode of Payment"), reqd: 1 };
	frappe.ui.form.on("Post Dated Cheque", {
		refresh(frm) {
			if (frm.is_new()) return;
			if (frm.doc.status === "Received") frm.add_custom_button(__("Deposit at the Bank"), () => act(frm, "deposit"));
			if (["Received", "Deposited"].includes(frm.doc.status)) {
				frm.add_custom_button(__("Cleared"), () => ask(frm, __("Cheque Cleared"), [MOP], "clear")).addClass("btn-primary");
				frm.add_custom_button(__("Bounced"), () => act(frm, "bounce"), __("More"));
			}
			if (["Received", "Bounced"].includes(frm.doc.status)) frm.add_custom_button(__("Return to the Customer"), () => act(frm, "return_to_customer"), __("More"));
		},
	});
})();
