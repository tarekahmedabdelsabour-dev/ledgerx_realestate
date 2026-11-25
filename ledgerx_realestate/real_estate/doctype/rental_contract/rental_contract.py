import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate

from ledgerx_realestate.engine import accounting, logic


class RentalContract(Document):
	def validate(self):
		if getdate(self.end_date) <= getdate(self.start_date):
			frappe.throw(_("The lease must end after it starts"))
		if flt(self.monthly_rent) <= 0:
			frappe.throw(_("Enter the monthly rent"))
		if self.is_new() and frappe.db.get_value("Property Unit", self.unit, "status") in ("Rented", "Contracted", "Reserved", "Blocked"):
			frappe.throw(_("The unit is not free to rent"))

	@frappe.whitelist(methods=["POST"])
	def activate(self):
		self.check_permission("write")
		if self.status != "Draft":
			frappe.throw(_("The lease is {0}").format(_(self.status)))
		if frappe.db.get_value("Property Unit", self.unit, "status") in ("Rented", "Contracted", "Reserved", "Blocked"):
			frappe.throw(_("The unit is not free to rent"))
		self.db_set("status", "Active")
		frappe.db.set_value("Property Unit", self.unit, "status", "Rented")

	@frappe.whitelist(methods=["POST"])
	def receive_deposit(self, mode_of_payment, reference=None):
		self.check_permission("write")
		if self.deposit_entry or flt(self.security_deposit) <= 0:
			frappe.throw(_("There is no deposit to receive"))
		pe = accounting.payment(self.tenant, self.security_deposit, accounting.money_account(mode_of_payment), remarks=_("Security deposit - {0}").format(self.unit),
			reference=reference or self.name)
		self.db_set("deposit_entry", pe)
		return pe

	@frappe.whitelist(methods=["POST"])
	def bill_due(self):
		"""Invoices every month that has started and was not billed yet. Safe to run again: it never bills a month twice."""
		self.check_permission("write")
		if self.status != "Active":
			return 0
		s = accounting.settings()
		project = frappe.db.get_value("Property Unit", self.unit, "project")
		n = 0
		for p in logic.rental_periods(self.start_date, self.end_date, self.last_billed, nowdate()):
			amount = logic.rent_for_period(self.monthly_rent, self.annual_increase_pct, self.start_date, p)
			inv = accounting.sales_invoice(self.tenant, [(accounting.item("Rent"), amount, accounting.need(s, "rental_income_account", "Rental Income Account"),
				_("Rent {0} - {1}").format(p, self.unit))], accounting.cost_center_of(project), _("Lease {0}").format(self.name), due_date=p, posting_date=p)
			self.append("invoices", {"period_start": p, "amount": amount, "sales_invoice": inv})
			self.last_billed = p
			self.save(ignore_permissions=True)
			n += 1
		return n

	def _free_unit(self):
		u = frappe.db.get_value("Property Unit", self.unit, ["status", "owner_customer"], as_dict=True)
		if u.status == "Rented":
			frappe.db.set_value("Property Unit", self.unit, "status", "Delivered" if u.owner_customer else "Available")

	@frappe.whitelist(methods=["POST"])
	def end_lease(self):
		self.check_permission("write")
		if self.status != "Active":
			frappe.throw(_("The lease is {0}").format(_(self.status)))
		self.db_set("status", "Ended")
		self._free_unit()

	@frappe.whitelist(methods=["POST"])
	def renew(self, new_end, new_rent=None):
		self.check_permission("write")
		if self.status != "Active":
			frappe.throw(_("The lease is {0}").format(_(self.status)))
		if getdate(new_end) <= getdate(self.end_date):
			frappe.throw(_("The new end date must be after the current one"))
		self.db_set("end_date", new_end)
		if flt(new_rent):
			self.db_set("monthly_rent", flt(new_rent))
