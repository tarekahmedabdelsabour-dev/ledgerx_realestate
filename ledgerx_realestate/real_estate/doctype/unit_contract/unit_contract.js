(() => {
	const act = (frm, method, args) => frm.call({ doc: frm.doc, method, args: args || {}, freeze: true }).then((r) => { frm.reload_doc(); return r; });
	const ask = (frm, title, fields, method) => {
		const d = new frappe.ui.Dialog({ title, fields, primary_action_label: __("Save"), primary_action(v) { d.hide(); act(frm, method, v); } });
		d.show();
	};
	const MOP = { fieldname: "mode_of_payment", fieldtype: "Link", options: "Mode of Payment", label: __("Mode of Payment"), reqd: 1 };
	frappe.ui.form.on("Unit Contract", {
		setup(frm) {
			frm.set_query("unit", () => ({ filters: { status: ["in", ["Available", "Reserved"]] } }));
			frm.set_query("payment_plan", () => ({ filters: { active: 1 } }));
			frm.set_query("reservation", () => ({ filters: { status: "Active" } }));
		},
		show_collection(frm) {
			const w = frm.fields_dict.schedule_html && frm.fields_dict.schedule_html.$wrapper;
			if (!w) return;
			if (!frm.doc.sales_invoice) { w.html(`<p class="text-muted">${__("The collection appears once the contract is confirmed.")}</p>`); return; }
			frappe.db.get_doc("Sales Invoice", frm.doc.sales_invoice).then((inv) => {
				const today = frappe.datetime.get_today();
				const rows = (inv.payment_schedule || []).map((r) => {
					const due = flt(r.payment_amount) - flt(r.paid_amount);
					const late = due > 0.005 && r.due_date < today;
					return `<tr><td>${frappe.datetime.str_to_user(r.due_date)}</td><td>${format_currency(r.payment_amount)}</td><td>${format_currency(r.paid_amount)}</td>
						<td>${due > 0.005 ? format_currency(due) : "✓"}</td><td>${late ? `<span class="indicator-pill red">${__("Late")}</span>` : ""}</td></tr>`;
				}).join("");
				w.html(`<p><b>${__("Paid")}:</b> ${format_currency(flt(inv.grand_total) - flt(inv.outstanding_amount))} &nbsp; <b>${__("Still Due")}:</b> ${format_currency(inv.outstanding_amount)}</p>
					<table class="table table-bordered"><thead><tr><th>${__("Due Date")}</th><th>${__("Amount")}</th><th>${__("Paid")}</th><th>${__("Still Due")}</th><th></th></tr></thead><tbody>${rows}</tbody></table>`);
			});
		},
		refresh(frm) {
			frm.events.show_collection(frm);
			if (frm.is_new()) return;
			if (frm.doc.status === "Draft") frm.add_custom_button(__("Confirm the Contract"), () => frappe.confirm(__("Create the invoice with the payment schedule and take the unit off the market?"), () => act(frm, "confirm"))).addClass("btn-primary");
			if (["Active", "Delivered"].includes(frm.doc.status)) {
				frm.add_custom_button(__("Receive Payment"), () => ask(frm, __("Receive Payment"), [MOP, { fieldname: "amount", fieldtype: "Currency", label: __("Amount"), reqd: 1 },
					{ fieldname: "reference", fieldtype: "Data", label: __("Reference") }], "receive_payment"), __("Money"));
				frm.add_custom_button(__("Post Dated Cheque"), () => frappe.new_doc("Post Dated Cheque", { contract: frm.doc.name }), __("Money"));
				frm.add_custom_button(__("Open Invoice"), () => frappe.set_route("Form", "Sales Invoice", frm.doc.sales_invoice));
			}
			if (frm.doc.status === "Active") {
				frm.add_custom_button(__("Schedule the Handover"), () => frappe.new_doc("Unit Handover", { contract: frm.doc.name }), __("Create"));
				frm.add_custom_button(__("Cancel the Contract"), () => ask(frm, __("Cancel the Contract"), [
					{ fieldname: "penalty_pct", fieldtype: "Percent", label: __("Penalty on What the Customer Paid (%)"), default: 0 },
					{ fieldname: "refund_mode", fieldtype: "Link", options: "Mode of Payment", label: __("Refund the Rest Through"), description: __("Leave empty to keep it as the customer's credit.") }], "cancel_contract"), __("More"));
			}
		},
	});
})();
