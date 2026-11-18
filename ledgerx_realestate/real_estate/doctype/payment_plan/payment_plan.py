import frappe
from frappe import _
from frappe.model.document import Document


class PaymentPlan(Document):
	def validate(self):
		total = (self.down_payment_pct or 0) + (self.delivery_pct or 0) + sum(r.percent or 0 for r in self.extras)
		if total > 100:
			frappe.throw(_("Down payment, delivery and extra payments add up to more than 100%"))
		if (self.installments or 0) < 1 and total < 100:
			frappe.throw(_("Add at least one installment"))
		if (self.interval_months or 0) < 1:
			frappe.throw(_("The months between installments must be at least 1"))
