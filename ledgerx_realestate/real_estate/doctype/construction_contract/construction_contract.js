(() => {
	const act = (frm, method, args) => frm.call({ doc: frm.doc, method, args: args || {}, freeze: true }).then((r) => { frm.reload_doc(); return r; });
	const ask = (frm, title, fields, method) => {
		const d = new frappe.ui.Dialog({ title, fields, primary_action_label: __("Save"), primary_action(v) { d.hide(); act(frm, method, v); } });
		d.show();
	};
	const MOP = { fieldname: "mode_of_payment", fieldtype: "Link", options: "Mode of Payment", label: __("Mode of Payment"), reqd: 1 };
	frappe.ui.form.on("Construction Contract", {
		setup(frm) { frm.set_query("boq", () => ({ filters: { project: frm.doc.project } })); },
		refresh(frm) {
			if (frm.is_new()) return;
			if (frm.doc.status === "Draft") frm.add_custom_button(__("Activate"), () => act(frm, "activate")).addClass("btn-primary");
			if (frm.doc.status === "Active") {
				frm.add_custom_button(__("New Progress Claim"), () => frappe.new_doc("Progress Claim", { construction_contract: frm.doc.name })).addClass("btn-primary");
				frm.add_custom_button(__("Pay an Advance"), () => ask(frm, __("Advance"), [MOP, { fieldname: "amount", fieldtype: "Currency", label: __("Amount"), reqd: 1 }], "pay_advance"), __("Money"));
				frm.add_custom_button(__("Mark Completed"), () => frappe.confirm(__("Mark this contract completed?"), () => act(frm, "complete")), __("More"));
			}
			frm.add_custom_button(__("Claims"), () => frappe.set_route("List", "Progress Claim", { construction_contract: frm.doc.name }), __("View"));
		},
	});
})();
