import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from ledgerx_realestate.engine import accounting, logic


class UnitContract(Document):
	def validate(self):
		if self.status != "Draft" and not self.is_new():
			return
		u = frappe.db.get_value("Property Unit", self.unit, ["status", "list_price", "project", "phase", "contract"], as_dict=True)
		if self.is_new():
			ok = u.status == "Available" or (u.status == "Reserved" and self.reservation and frappe.db.get_value("Unit Reservation", self.reservation, "unit") == self.unit)
			if not ok:
				frappe.throw(_("The unit is {0}").format(_(u.status)))
		if not flt(u.list_price):
			frappe.throw(_("The unit has no price: apply a price list or enter it on the unit"))
		self.list_price = u.list_price
		self._plan(u)
		if flt(self.discount) > flt(self.list_price):
			frappe.throw(_("The discount is more than the price"))
		s = accounting.settings()
		t = logic.contract_totals(self.list_price, self.discount, self.markup_pct, s.vat_rate, self.deposit_pct)
		self.net, self.markup, self.price, self.deposit, self.vat, self.total = t["net"], t["markup"], t["price"], t["deposit"], t["vat"], t["total"]
		self._schedule()
		if flt(self.commission_pct) < 0 or flt(self.commission_pct) > 100:
			frappe.throw(_("The commission must be between 0 and 100 percent"))
		if flt(self.discount) < 0:
			frappe.throw(_("The discount cannot be negative"))
		if self.broker and not flt(self.commission_pct):
			self.commission_pct = frappe.db.get_value("Real Estate Broker", self.broker, "commission_pct") or s.commission_pct

	def _plan(self, u):
		before = None if self.is_new() else self.get_doc_before_save()
		if not self.is_new() and before and before.payment_plan == self.payment_plan:
			return
		p = frappe.get_doc("Payment Plan", self.payment_plan)
		if not p.active:
			frappe.throw(_("The payment plan {0} is not active").format(p.name))
		if p.project and p.project != u.project:
			frappe.throw(_("The payment plan belongs to another project"))
		self.down_payment_pct, self.delivery_pct, self.markup_pct = p.down_payment_pct, p.delivery_pct, p.markup_pct
		self.deposit_pct, self.installments = p.maintenance_deposit_pct, p.installments
		self.interval_months, self.first_after_months = p.interval_months, p.first_after_months
		self.set("extras", [])
		for e in p.extras:
			self.append("extras", {"months": e.months, "percent": e.percent})
		if not self.delivery_date and u.phase:
			self.delivery_date = frappe.db.get_value("Project Phase", u.phase, "delivery_date")

	def _schedule(self):
		if (flt(self.delivery_pct) or flt(self.deposit)) and not self.delivery_date:
			frappe.throw(_("Enter the delivery date: the delivery payment and the maintenance deposit are due then"))
		fixed = [(self.deposit, self.delivery_date, "Maintenance Deposit")] if flt(self.deposit) else []
		try:
			rows = logic.plan_schedule(self.total, self.contract_date, self.down_payment_pct, self.installments, self.interval_months,
				[(e.percent, e.months) for e in self.extras], self.delivery_pct, self.delivery_date, fixed, self.first_after_months)
		except ValueError as e:
			frappe.throw(_("The payment plan does not add up: {0}").format(str(e)))
		self.set("schedule", [])
		for d, a, l in rows:
			self.append("schedule", {"due_date": d, "amount": a, "label": _(l)})

	def _need(self, *statuses):
		if self.status not in statuses:
			frappe.throw(_("The contract is {0}").format(_(self.status)))

	@frappe.whitelist(methods=["POST"])
	def confirm(self):
		"""One invoice for the whole contract with the payment schedule on it. The reservation deposit and any earlier payment are applied."""
		self.check_permission("write")
		self._need("Draft")
		s = accounting.settings()
		cc = accounting.cost_center_of(self.project)
		lines = [(accounting.item("Unit Sale"), self.price, accounting.need(s, "sales_income_account", "Unit Sales Income Account"),
			f"{self.unit} - {self.customer}")]
		if flt(self.deposit):
			lines.append((accounting.item("Maintenance Deposit"), self.deposit, accounting.need(s, "deposit_account", "Maintenance Deposit Account"),
				_("Maintenance deposit - {0}").format(self.unit)))
		inv = accounting.sales_invoice(self.customer, lines, cc, _("Contract {0} - {1}").format(self.name, self.unit), due_date=self.schedule[0].due_date,
			schedule=[(r.due_date, r.amount) for r in self.schedule], vat=self.vat, apply_advances=True, posting_date=self.contract_date)
		self.db_set({"status": "Active", "sales_invoice": inv})
		frappe.db.set_value("Property Unit", self.unit, {"status": "Contracted", "contract": self.name, "owner_customer": self.customer})
		if self.reservation:
			frappe.db.set_value("Unit Reservation", self.reservation, {"status": "Converted", "contract": self.name})
		self._commissions(s)
		return inv

	def _commissions(self, s):
		if self.broker and flt(self.commission_pct):
			frappe.get_doc({"doctype": "Sales Commission", "contract": self.name, "party_type": "Broker", "broker": self.broker, "base_amount": self.price,
				"pct": self.commission_pct, "amount": logic.commission(self.price, self.commission_pct)}).insert(ignore_permissions=True)
		if self.salesman and flt(s.salesman_commission_pct):
			frappe.get_doc({"doctype": "Sales Commission", "contract": self.name, "party_type": "Employee", "employee": self.salesman, "base_amount": self.price,
				"pct": s.salesman_commission_pct, "amount": logic.commission(self.price, s.salesman_commission_pct)}).insert(ignore_permissions=True)

	@frappe.whitelist(methods=["POST"])
	def receive_payment(self, mode_of_payment, amount, reference=None):
		self.check_permission("write")
		self._need("Active", "Delivered")
		out = flt(frappe.db.get_value("Sales Invoice", self.sales_invoice, "outstanding_amount"))
		amount = flt(amount)
		if amount <= 0 or amount > out + 0.005:
			frappe.throw(_("The amount must be above zero and not more than the {0} still due").format(out))
		return accounting.payment(self.customer, amount, accounting.money_account(mode_of_payment), self.sales_invoice,
			_("Contract {0} - {1}").format(self.name, self.unit), reference=reference)

	@frappe.whitelist(methods=["POST"])
	def cancel_contract(self, penalty_pct=0, refund_mode=None):
		"""Cancel an active contract: a credit note for the invoice, a penalty invoice on what the customer paid, and (with a mode of payment) the rest refunded.
		The unit goes back on sale."""
		self.check_permission("write")
		self._need("Active")
		penalty_pct = flt(penalty_pct)
		if penalty_pct < 0 or penalty_pct > 100:
			frappe.throw(_("The penalty must be between 0 and 100 percent"))
		if frappe.db.exists("Unit Handover", {"contract": self.name, "status": "Completed"}):
			frappe.throw(_("The unit was already handed over"))
		from erpnext.controllers.sales_and_purchase_return import make_return_doc

		s = accounting.settings()
		paid = flt(frappe.db.get_value("Sales Invoice", self.sales_invoice, "grand_total")) - flt(frappe.db.get_value("Sales Invoice", self.sales_invoice, "outstanding_amount"))
		ret = make_return_doc("Sales Invoice", self.sales_invoice)
		ret.insert(ignore_permissions=True)
		ret.submit()
		penalty = logic.r2(paid * flt(penalty_pct) / 100)
		if penalty:
			accounting.sales_invoice(self.customer, [(accounting.item("Cancellation Penalty"), penalty, accounting.need(s, "late_fee_income_account", "Late Fee Income Account"),
				_("Cancellation penalty - {0}").format(self.name))], accounting.cost_center_of(self.project), _("Cancellation of {0}").format(self.name), apply_advances=True)
		if refund_mode and paid - penalty > 0.005:
			accounting.payment(self.customer, paid - penalty, accounting.money_account(refund_mode), remarks=_("Refund - contract {0}").format(self.name), refund=True)
		self.db_set({"status": "Cancelled", "return_invoice": ret.name})
		frappe.db.set_value("Property Unit", self.unit, {"status": "Available", "contract": None, "owner_customer": None})
		for c in frappe.get_all("Sales Commission", filters={"contract": self.name, "status": ["in", ["Pending", "Due"]]}, pluck="name"):
			frappe.db.set_value("Sales Commission", c, "status", "Cancelled")
		return ret.name
