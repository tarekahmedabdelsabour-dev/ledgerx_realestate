import frappe
from frappe import _
from frappe.model.document import Document


class OwnersAssociation(Document):
	def validate(self):
		if self.building and frappe.db.get_value("Building", self.building, "project") != self.project:
			frappe.throw(_("The building belongs to another project"))
		if not (self.rate_per_m2 or self.fixed_fee):
			frappe.throw(_("Enter the monthly charge: per m² or a fixed amount"))
