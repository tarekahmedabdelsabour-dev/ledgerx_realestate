import frappe
from frappe import _
from frappe.model.document import Document

from ledgerx_realestate.engine import logic


class UnitPriceList(Document):
	def validate(self):
		seen = set()
		for r in self.rows:
			if r.unit_type in seen:
				frappe.throw(_("Row {0}: the unit type is listed twice").format(r.idx))
			seen.add(r.unit_type)

	@frappe.whitelist()
	def apply(self):
		"""Set the price of every available unit of the project: built area x price + garden area x price, plus the unit's own premium."""
		by = {r.unit_type: r for r in self.rows}
		n = 0
		for u in frappe.get_all("Property Unit", filters={"project": self.project, "status": "Available", "unit_type": ["in", list(by)]},
				fields=["name", "unit_type", "area_built", "area_garden", "premium_pct"]):
			r = by[u.unit_type]
			frappe.db.set_value("Property Unit", u.name, "list_price", logic.unit_price(u.area_built, u.area_garden, r.per_m2, r.garden_per_m2, u.premium_pct))
			n += 1
		return n
