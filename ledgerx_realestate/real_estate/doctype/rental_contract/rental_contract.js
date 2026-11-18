(() => {
	const act = (frm, method, args) => frm.call({ doc: frm.doc, method, args: args || {}, freeze: true }).then((r) => { frm.reload_doc(); return r; });
	const ask = (frm, title, fields, method) => {
		const d = new frappe.ui.Dialog({ title, fields, primary_action_label: __("Save"), primary_action(v) { d.hide(); act(frm, method, v); } });
		d.show();
	};
	const MOP = { fieldname: "mode_of_payment", fieldtype: "Link", options: "Mode of Payment", label: __("Mode of Payment"), reqd: 1 };
	frappe.ui.form.on("Rental Contract", {
		setup(frm) { frm.set_query("unit", () => ({ filters: { status: ["in", ["Available", "Delivered"]] } })); },
		refresh(frm) {
			if (frm.is_new()) return;
			if (frm.doc.status === "Draft") frm.add_custom_button(__("Activate the Lease"), () => act(frm, "activate")).addClass("btn-primary");
			if (!frm.doc.deposit_entry && frm.doc.security_deposit > 0 && frm.doc.status !== "Cancelled")
				frm.add_custom_button(__("Receive the Deposit"), () => ask(frm, __("Security Deposit"), [MOP, { fieldname: "reference", fieldtype: "Data", label: __("Reference") }], "receive_deposit"), __("Money"));
			if (frm.doc.status === "Active") {
				frm.add_custom_button(__("Invoice Due Months"), () => act(frm, "bill_due").then((r) => frappe.show_alert({ message: __("{0} invoices", [r.message]), indicator: "green" })), __("Money"));
				frm.add_custom_button(__("Renew"), () => ask(frm, __("Renew"), [{ fieldname: "new_end", fieldtype: "Date", label: __("New End Date"), reqd: 1 },
					{ fieldname: "new_rent", fieldtype: "Currency", label: __("New Monthly Rent") }], "renew"), __("More"));
				frm.add_custom_button(__("End the Lease"), () => frappe.confirm(__("End this lease?"), () => act(frm, "end_lease")), __("More"));
			}
		},
	});
})();
