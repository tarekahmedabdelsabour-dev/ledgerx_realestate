import frappe
from frappe import _
from frappe.model.document import Document


class PropertyUnit(Document):
	def validate(self):
		if self.category != "Land" and not (self.area_built or 0) > 0:
			frappe.throw(_("Enter the built area"))
		if self.building and frappe.db.get_value("Building", self.building, "project") != self.project:
			frappe.throw(_("The building belongs to another project"))
		if self.phase and frappe.db.get_value("Project Phase", self.phase, "project") != self.project:
			frappe.throw(_("The phase belongs to another project"))
		if not self.is_new():
			before = self.get_doc_before_save()
			if before and before.list_price != self.list_price and self.status not in ("Available", "Blocked"):
				frappe.throw(_("The price of a unit that is not available cannot be changed: the contract keeps its own price"))

	@frappe.whitelist()
	def set_blocked(self, blocked):
		"""Take a unit off sale (or put it back) without a contract."""
		blocked = int(blocked)
		if blocked and self.status != "Available":
			frappe.throw(_("Only an available unit can be blocked"))
		if not blocked and self.status != "Blocked":
			frappe.throw(_("The unit is not blocked"))
		self.db_set("status", "Blocked" if blocked else "Available")
