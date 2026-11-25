import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate

from ledgerx_realestate.engine import accounting, logic


class SalesCommission(Document):
	def validate(self):
		if self.party_type == "Broker" and not self.broker:
			frappe.throw(_("Choose the broker"))
		if self.party_type == "Employee" and not self.employee:
			frappe.throw(_("Choose the salesman"))
		if self.status in ("Pending", "Due"):
			self.amount = logic.commission(self.base_amount, self.pct) if self.base_amount and self.pct else self.amount

	@frappe.whitelist(methods=["POST"])
	def pay(self):
		"""A broker is invoiced through his supplier account (a purchase invoice to pay); a salesman goes to payroll as an additional salary."""
		self.check_permission("write")
		if self.status not in ("Pending", "Due"):
			frappe.throw(_("The commission is {0}").format(_(self.status)))
		if self.status == "Pending" and not frappe.flags.in_test:
			frappe.msgprint(_("The customer has not yet paid the share that makes this commission due"), indicator="orange")
		s = accounting.settings()
		project = frappe.db.get_value("Unit Contract", self.contract, "project")
		cc = accounting.cost_center_of(project)
		if self.party_type == "Broker":
			supplier = frappe.db.get_value("Real Estate Broker", self.broker, "supplier")
			if not supplier:
				frappe.throw(_("The broker has no supplier account"))
			inv = frappe.new_doc("Purchase Invoice")
			inv.update({"supplier": supplier, "company": s.company, "posting_date": nowdate(), "cost_center": cc, "update_stock": 0,
				"remarks": _("Commission - contract {0}").format(self.contract)})
			inv.append("items", {"item_code": accounting.item("Broker Commission"), "qty": 1, "rate": flt(self.amount), "cost_center": cc,
				"expense_account": accounting.need(s, "commission_expense_account", "Commission Expense Account")})
			inv.insert(ignore_permissions=True)
			inv.submit()
			self.db_set({"purchase_invoice": inv.name, "status": "Invoiced"})
			return inv.name
		sal = frappe.get_doc({"doctype": "Additional Salary", "employee": self.employee, "company": s.company, "salary_component": s.salary_component,
			"amount": flt(self.amount), "payroll_date": nowdate(), "overwrite_salary_structure_amount": 1}).insert(ignore_permissions=True)
		sal.submit()
		self.db_set({"additional_salary": sal.name, "status": "Invoiced"})
		return sal.name
