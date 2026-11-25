import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate

from ledgerx_realestate.engine import accounting


class MaintenanceRequest(Document):
	def validate(self):
		u = frappe.db.get_value("Property Unit", self.unit, ["owner_customer", "warranty_end", "project"], as_dict=True)
		if not self.customer:
			self.customer = u.owner_customer
		self.under_warranty = 1 if u.warranty_end and getdate(u.warranty_end) >= getdate(self.reported_on or nowdate()) else 0
		if self.status in ("Assigned", "In Progress") and not (self.assigned_employee or self.assigned_supplier):
			frappe.throw(_("Choose who does the work"))

	@frappe.whitelist(methods=["POST"])
	def invoice_owner(self):
		"""Bills the owner for work that is not covered by the warranty (or for the amount entered)."""
		self.check_permission("write")
		if flt(self.charge) <= 0:
			frappe.throw(_("Enter the amount to charge"))
		if self.sales_invoice:
			frappe.throw(_("Already invoiced"))
		if not self.customer:
			frappe.throw(_("The unit has no owner"))
		s = accounting.settings()
		project = frappe.db.get_value("Property Unit", self.unit, "project")
		inv = accounting.sales_invoice(self.customer, [(accounting.item("Maintenance Work"), self.charge, accounting.need(s, "maintenance_income_account", "Maintenance Income Account"),
			f"{self.category} - {self.unit}")], accounting.cost_center_of(project), _("Maintenance request {0}").format(self.name))
		self.db_set("sales_invoice", inv)
		return inv
