import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt, getdate, nowdate

from ledgerx_realestate.engine import accounting


class UnitReservation(Document):
	def validate(self):
		if self.is_new():
			if frappe.db.get_value("Property Unit", self.unit, "status") != "Available":
				frappe.throw(_("The unit is not available"))
			if not self.valid_until:
				self.valid_until = add_days(nowdate(), int(accounting.settings().reservation_days or 7))
		if getdate(self.valid_until) < getdate(nowdate()) and self.is_new():
			frappe.throw(_("The reservation date is in the past"))

	def after_insert(self):
		frappe.db.set_value("Property Unit", self.unit, "status", "Reserved")

	@frappe.whitelist(methods=["POST"])
	def receive_deposit(self, mode_of_payment, amount, reference=None):
		"""The deposit stays as the customer's advance: the contract invoice uses it."""
		self.check_permission("write")
		if self.status != "Active":
			frappe.throw(_("The reservation is {0}").format(_(self.status)))
		if self.deposit_entry:
			frappe.throw(_("The deposit is already received"))
		pe = accounting.payment(self.customer, amount, accounting.money_account(mode_of_payment), remarks=_("Reservation deposit - {0}").format(self.unit),
			reference=reference or self.name)
		self.db_set({"deposit_entry": pe, "deposit": flt(amount)})
		return pe

	def _free(self, status):
		self.db_set("status", status)
		if frappe.db.get_value("Property Unit", self.unit, "status") == "Reserved":
			frappe.db.set_value("Property Unit", self.unit, "status", "Available")

	@frappe.whitelist(methods=["POST"])
	def cancel_reservation(self, refund_mode=None):
		"""Frees the unit. With a mode of payment the deposit is given back; without, it stays as the customer's credit."""
		self.check_permission("write")
		if self.status != "Active":
			frappe.throw(_("The reservation is {0}").format(_(self.status)))
		if refund_mode and self.deposit_entry:
			accounting.payment(self.customer, self.deposit, accounting.money_account(refund_mode), remarks=_("Deposit refund - {0}").format(self.name), refund=True)
		self._free("Cancelled")
