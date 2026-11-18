import frappe
from frappe.model.document import Document


class RealEstateBroker(Document):
	def after_insert(self):
		try:
			group = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name")
			s = frappe.get_doc({"doctype": "Supplier", "supplier_name": f"{self.broker_name} (Broker)" if frappe.db.exists("Supplier", self.broker_name) else self.broker_name,
				"supplier_group": group, "supplier_type": "Company" if self.broker_type == "Company" else "Individual"}).insert(ignore_permissions=True)
			self.db_set("supplier", s.name)
		except Exception:
			frappe.log_error(title="Real estate: could not create the supplier of a broker")
