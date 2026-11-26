(() => {
	const act = (frm, method, args) => frm.call({ doc: frm.doc, method, args: args || {}, freeze: true }).then((r) => { frm.reload_doc(); return r; });
	const ask = (frm, title, fields, method) => {
		const d = new frappe.ui.Dialog({ title, fields, primary_action_label: __("Save"), primary_action(v) { d.hide(); act(frm, method, v); } });
		d.show();
	};
	const MOP = { fieldname: "mode_of_payment", fieldtype: "Link", options: "Mode of Payment", label: __("Mode of Payment"), reqd: 1 };
	frappe.ui.form.on("Property Maintenance Request", {
		refresh(frm) {
			if (frm.is_new()) return;
			if (!frm.doc.sales_invoice && frm.doc.charge > 0) frm.add_custom_button(__("Invoice the Owner"), () => act(frm, "invoice_owner")).addClass("btn-primary");
			if (frm.doc.sales_invoice) frm.add_custom_button(__("Open Invoice"), () => frappe.set_route("Form", "Sales Invoice", frm.doc.sales_invoice));
		},
	});
})();
