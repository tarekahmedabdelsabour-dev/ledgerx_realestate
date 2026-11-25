import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from ledgerx_realestate.engine import accounting, logic


class ProgressClaim(Document):
	def validate(self):
		if self.status != "Draft":
			return
		c = frappe.db.get_value("Construction Contract", self.construction_contract,
			["status", "contract_value", "claimed_gross", "last_pct", "retention_pct", "advance_pct", "advance_paid"], as_dict=True)
		if c.status != "Active":
			frappe.throw(_("The construction contract is {0}").format(_(c.status)))
		if flt(self.cumulative_pct) <= flt(c.last_pct) and self.is_new():
			frappe.throw(_("The completion must be above what was already claimed ({0}%)").format(c.last_pct))
		recovered = flt(frappe.db.sql("""select sum(advance_recovery) from `tabProgress Claim` where construction_contract = %s and status = 'Approved'""",
			self.construction_contract)[0][0])
		try:
			r = logic.progress_claim(c.contract_value, self.cumulative_pct, c.claimed_gross, c.retention_pct, c.advance_pct, flt(c.advance_paid) - recovered, self.penalties)
		except ValueError as e:
			frappe.throw(_("The claim does not add up: {0}").format(str(e)))
		self.contract_value, self.cumulative_value, self.previous_gross = c.contract_value, r["cumulative"], c.claimed_gross
		self.gross, self.retention, self.advance_recovery, self.net = r["gross"], r["retention"], r["advance"], r["net"]
		if self.net < 0:
			frappe.throw(_("The deductions are more than the claim"))

	@frappe.whitelist(methods=["POST"])
	def approve(self):
		"""Posts the claim as a purchase invoice to the contractor: retention and penalties are deducted, the advance is set against it."""
		self.check_permission("write")
		if self.status != "Draft":
			frappe.throw(_("The claim is {0}").format(_(self.status)))
		s = accounting.settings()
		cc = accounting.cost_center_of(self.project)
		cost = accounting.need(s, "construction_cost_account", "Construction Cost Account")
		inv = frappe.new_doc("Purchase Invoice")
		inv.update({"supplier": self.contractor, "company": s.company, "posting_date": self.claim_date, "cost_center": cc, "update_stock": 0,
			"allocate_advances_automatically": 0, "remarks": _("Progress claim {0} - {1}").format(self.name, self.construction_contract)})
		inv.append("items", {"item_code": accounting.item("Construction Work"), "qty": 1, "rate": flt(self.gross), "cost_center": cc, "expense_account": cost,
			"description": _("Work to {0}% - {1}").format(self.cumulative_pct, self.construction_contract)})
		if flt(self.retention):
			inv.append("taxes", {"category": "Total", "add_deduct_tax": "Deduct", "charge_type": "Actual", "account_head": accounting.need(s, "retention_account", "Retention Payable Account"),
				"description": _("Retention"), "tax_amount": flt(self.retention), "cost_center": cc})
		if flt(self.penalties):
			inv.append("taxes", {"category": "Total", "add_deduct_tax": "Deduct", "charge_type": "Actual", "account_head": cost, "description": _("Penalties"),
				"tax_amount": flt(self.penalties), "cost_center": cc})
		inv.insert(ignore_permissions=True)
		if flt(self.advance_recovery):
			inv.set_advances()
			left = flt(self.advance_recovery)
			for a in list(inv.get("advances") or []):
				take = min(flt(a.allocated_amount), left)
				if take <= 0:
					inv.remove(a)
				else:
					a.allocated_amount = take
					left -= take
			inv.save(ignore_permissions=True)
		inv.submit()
		self.db_set({"status": "Approved", "purchase_invoice": inv.name})
		frappe.db.set_value("Construction Contract", self.construction_contract,
			{"claimed_gross": flt(self.previous_gross) + flt(self.gross), "last_pct": self.cumulative_pct})
		return inv.name

	@frappe.whitelist(methods=["POST"])
	def cancel_draft(self):
		self.check_permission("write")
		if self.status != "Draft":
			frappe.throw(_("The claim is {0}").format(_(self.status)))
		self.db_set("status", "Cancelled")
