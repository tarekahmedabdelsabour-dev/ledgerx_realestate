import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt



class PostDatedCheque(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Enter the cheque amount"))
		if frappe.db.get_value("Unit Contract", self.contract, "status") not in ("Active", "Delivered"):
			frappe.throw(_("The contract is not active"))

	def _need(self, *statuses):
		if self.status not in statuses:
			frappe.throw(_("The cheque is {0}").format(_(self.status)))

	@frappe.whitelist(methods=["POST"])
	def deposit(self):
		self.check_permission("write")
		self._need("Received")
		self.db_set("status", "Deposited")

	@frappe.whitelist(methods=["POST"])
	def clear(self, mode_of_payment):
		"""The bank paid it: the money is received on the contract invoice."""
		self.check_permission("write")
		self._need("Received", "Deposited")
		c = frappe.get_doc("Unit Contract", self.contract)
		pe = c.receive_payment(mode_of_payment, self.amount, reference=self.cheque_number)
		self.db_set({"status": "Cleared", "payment_entry": pe})
		return pe

	@frappe.whitelist(methods=["POST"])
	def bounce(self):
		self.check_permission("write")
		self._need("Received", "Deposited")
		self.db_set("status", "Bounced")

	@frappe.whitelist(methods=["POST"])
	def return_to_customer(self):
		self.check_permission("write")
		self._need("Received", "Bounced")
		self.db_set("status", "Returned")
