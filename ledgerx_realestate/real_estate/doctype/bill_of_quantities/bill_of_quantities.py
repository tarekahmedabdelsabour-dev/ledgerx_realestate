import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from ledgerx_realestate.engine import logic


class BillofQuantities(Document):
	def validate(self):
		for r in self.items:
			r.amount = logic.r2(flt(r.quantity) * flt(r.rate))
		self.total_budget = logic.r2(sum(r.amount for r in self.items))

	@frappe.whitelist(methods=["POST"])
	def approve(self):
		self.check_permission("write")
		if self.status != "Draft":
			frappe.throw(_("The bill of quantities is {0}").format(_(self.status)))
		self.db_set("status", "Approved")
