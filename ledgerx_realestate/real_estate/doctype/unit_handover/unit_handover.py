import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from ledgerx_realestate.engine import accounting, logic

DEFAULT_CHECKLIST = ("Doors and windows", "Electrical points and switches", "Plumbing and sanitary", "Walls and paint", "Floors and tiles", "Kitchen", "Air conditioning", "Meters")


class UnitHandover(Document):
	def validate(self):
		if self.status != "Draft" and self.status != "Scheduled" and not self.is_new():
			return
		c = frappe.db.get_value("Unit Contract", self.contract, ["status", "unit"], as_dict=True)
		if c.status != "Active":
			frappe.throw(_("The contract is {0}").format(_(c.status)))
		if self.is_new():
			if frappe.db.exists("Unit Handover", {"contract": self.contract, "status": ["!=", "Cancelled"]}):
				frappe.throw(_("This contract already has a handover"))
			if not self.checklist:
				for it in DEFAULT_CHECKLIST:
					self.append("checklist", {"item": _(it)})
		if not self.warranty_months:
			self.warranty_months = accounting.settings().warranty_months

	@frappe.whitelist()
	def complete(self):
		"""Hands the unit over: it becomes delivered, the warranty starts, and (by default) everything due must have been paid."""
		if self.status != "Scheduled":
			frappe.throw(_("The handover is {0}").format(_(self.status)))
		c = frappe.get_doc("Unit Contract", self.contract)
		if accounting.settings().handover_needs_payment:
			st = accounting.invoice_state(c.sales_invoice)
			due = sum(flt(r.payment_amount) - flt(r.paid_amount) for r in st["rows"] if getdate(r.due_date) <= getdate(self.handover_date))
			if due > 0.005:
				frappe.throw(_("The customer still owes {0} that is due: collect it before the handover").format(due))
		bad = [r.item for r in self.checklist if not r.ok]
		if bad:
			frappe.msgprint(_("Not accepted: {0}").format(", ".join(bad)), indicator="orange")
		end = str(logic.add_months(self.handover_date, int(self.warranty_months or 0)))
		self.db_set({"status": "Completed", "warranty_end": end})
		frappe.db.set_value("Property Unit", c.unit, {"status": "Delivered", "warranty_end": end, "owner_customer": c.customer})
		c.db_set("status", "Delivered")

	@frappe.whitelist()
	def cancel_handover(self):
		if self.status != "Scheduled":
			frappe.throw(_("The handover is {0}").format(_(self.status)))
		self.db_set("status", "Cancelled")
