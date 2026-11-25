import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from ledgerx_realestate.engine import accounting


class ConstructionContract(Document):
	def validate(self):
		if flt(self.contract_value) <= 0:
			frappe.throw(_("Enter the contract value"))
		if flt(self.retention_pct) + flt(self.advance_pct) >= 100:
			frappe.throw(_("Retention and advance recovery leave nothing to pay"))
		if self.boq and frappe.db.get_value("Bill of Quantities", self.boq, "project") != self.project:
			frappe.throw(_("The bill of quantities belongs to another project"))

	@frappe.whitelist(methods=["POST"])
	def activate(self):
		self.check_permission("write")
		if self.status != "Draft":
			frappe.throw(_("The contract is {0}").format(_(self.status)))
		self.db_set("status", "Active")

	@frappe.whitelist(methods=["POST"])
	def complete(self):
		self.check_permission("write")
		if self.status != "Active":
			frappe.throw(_("The contract is {0}").format(_(self.status)))
		self.db_set("status", "Completed")

	@frappe.whitelist(methods=["POST"])
	def pay_advance(self, mode_of_payment, amount):
		"""An advance to the contractor: recovered from his next claims by the percentage set on the contract."""
		self.check_permission("write")
		if self.status != "Active":
			frappe.throw(_("The contract is {0}").format(_(self.status)))
		amount = flt(amount)
		if amount <= 0:
			frappe.throw(_("Enter the advance amount"))
		pe = accounting.supplier_payment(self.contractor, amount, accounting.money_account(mode_of_payment), _("Advance - {0}").format(self.name))
		self.db_set("advance_paid", flt(self.advance_paid) + amount)
		return pe
