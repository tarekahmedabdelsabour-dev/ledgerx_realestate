import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from ledgerx_realestate.engine import accounting


class RealEstateProject(Document):
	def validate(self):
		if self.start_date and self.expected_end_date and getdate(self.expected_end_date) < getdate(self.start_date):
			frappe.throw(_("The project ends before it starts"))

	def after_insert(self):
		try:
			p = frappe.get_doc({"doctype": "Project", "project_name": self.project_name, "company": accounting.settings().company or None,
				"cost_center": self.cost_center, "expected_start_date": self.start_date, "expected_end_date": self.expected_end_date}).insert(ignore_permissions=True)
			self.db_set("erp_project", p.name)
		except Exception:
			frappe.log_error(title="Real estate: could not create the project record")
