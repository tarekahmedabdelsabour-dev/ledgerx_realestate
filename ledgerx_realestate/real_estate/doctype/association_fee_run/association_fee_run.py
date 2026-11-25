import frappe
from frappe import _
from frappe.model.document import Document

from ledgerx_realestate.engine import accounting, logic


class AssociationFeeRun(Document):
	def validate(self):
		if self.is_new() and frappe.db.exists("Association Fee Run", {"association": self.association, "period": self.period, "status": "Posted"}):
			frappe.throw(_("The charges of {0} were already posted for {1}").format(self.association, self.period))

	@frappe.whitelist(methods=["POST"])
	def generate(self):
		"""One invoice to the owner of every delivered unit of the association."""
		self.check_permission("write")
		if self.status != "Draft":
			frappe.throw(_("The run is {0}").format(_(self.status)))
		a = frappe.get_doc("Owners Association", self.association)
		if not a.active:
			frappe.throw(_("The association is not active"))
		s = accounting.settings()
		f = {"project": a.project, "status": ["in", ["Delivered", "Rented"]], "owner_customer": ["is", "set"]}
		if a.building:
			f["building"] = a.building
		self.set("lines", [])
		total = 0
		for u in frappe.get_all("Property Unit", filters=f, fields=["name", "area_built", "owner_customer"]):
			amount = logic.service_charge(u.area_built, a.rate_per_m2, a.fixed_fee)
			if amount <= 0:
				continue
			inv = accounting.sales_invoice(u.owner_customer, [(accounting.item("Service Charge"), amount, accounting.need(s, "service_income_account", "Service Charge Income Account"),
				_("Service charge {0} - {1}").format(self.period, u.name))], accounting.cost_center_of(a.project), _("{0} - {1}").format(a.name, self.period),
				posting_date=self.posting_date)
			self.append("lines", {"unit": u.name, "customer": u.owner_customer, "amount": amount, "sales_invoice": inv})
			total += amount
		self.invoices_count, self.total, self.status = len(self.lines), logic.r2(total), "Posted"
		self.save(ignore_permissions=True)
		return self.invoices_count
