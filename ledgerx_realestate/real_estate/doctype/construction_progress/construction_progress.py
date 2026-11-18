import frappe
from frappe import _
from frappe.model.document import Document


class ConstructionProgress(Document):
	def validate(self):
		if self.building and frappe.db.get_value("Building", self.building, "project") != self.project:
			frappe.throw(_("The building belongs to another project"))

	def on_update(self):
		"""The building shows the completion of its latest record."""
		if self.building:
			last = frappe.get_all("Construction Progress", filters={"building": self.building}, fields=["completion_pct"], order_by="progress_date desc, creation desc", limit=1)
			if last:
				frappe.db.set_value("Building", self.building, "progress_pct", last[0].completion_pct)
