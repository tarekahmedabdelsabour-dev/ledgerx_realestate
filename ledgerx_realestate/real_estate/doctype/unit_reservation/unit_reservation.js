(() => {
	const act = (frm, method, args) => frm.call({ doc: frm.doc, method, args: args || {}, freeze: true }).then((r) => { frm.reload_doc(); return r; });
	const ask = (frm, title, fields, method) => {
		const d = new frappe.ui.Dialog({ title, fields, primary_action_label: __("Save"), primary_action(v) { d.hide(); act(frm, method, v); } });
		d.show();
	};
	const MOP = { fieldname: "mode_of_payment", fieldtype: "Link", options: "Mode of Payment", label: __("Mode of Payment"), reqd: 1 };
	frappe.ui.form.on("Unit Reservation", {
		setup(frm) { frm.set_query("unit", () => ({ filters: { status: "Available" } })); },
		refresh(frm) {
			if (frm.is_new()) return;
			if (frm.doc.status === "Active") {
				if (!frm.doc.deposit_entry) frm.add_custom_button(__("Receive the Deposit"), () => ask(frm, __("Deposit"), [MOP,
					{ fieldname: "amount", fieldtype: "Currency", label: __("Amount"), default: frm.doc.deposit, reqd: 1 }, { fieldname: "reference", fieldtype: "Data", label: __("Reference") }], "receive_deposit"), __("Money"));
				frm.add_custom_button(__("Make the Contract"), () => frappe.new_doc("Unit Contract", { unit: frm.doc.unit, customer: frm.doc.customer, reservation: frm.doc.name,
					broker: frm.doc.broker, salesman: frm.doc.salesman })).addClass("btn-primary");
				frm.add_custom_button(__("Cancel the Reservation"), () => ask(frm, __("Cancel"), [{ fieldname: "refund_mode", fieldtype: "Link", options: "Mode of Payment",
					label: __("Refund the Deposit Through"), description: __("Leave empty to keep the deposit as the customer's credit.") }], "cancel_reservation"), __("More"));
			}
			if (frm.doc.contract) frm.add_custom_button(__("Open Contract"), () => frappe.set_route("Form", "Unit Contract", frm.doc.contract));
		},
	});
})();
