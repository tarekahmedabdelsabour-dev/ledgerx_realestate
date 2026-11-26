"""Shows the real estate documents in the "Connections" panel of the records they belong to."""
from frappe import _


def _group(data, label, items, fields=None):
	data = data or {}
	data.setdefault("transactions", [])
	data["transactions"].append({"label": _(label), "items": items})
	if fields:
		data.setdefault("non_standard_fieldnames", {}).update(fields)
	return data


def customer(data=None):
	return _group(data, "Real Estate", ["Unit Reservation", "Unit Contract", "Property Maintenance Request"], {"Unit Contract": "customer"})


def supplier(data=None):
	return _group(data, "Real Estate", ["Construction Contract", "Progress Claim"], {"Construction Contract": "contractor", "Progress Claim": "contractor"})


def employee(data=None):
	return _group(data, "Real Estate", ["Unit Contract", "Unit Reservation"], {"Unit Contract": "salesman", "Unit Reservation": "salesman"})


def sales_invoice(data=None):
	return _group(data, "Real Estate", ["Unit Contract", "Property Maintenance Request"], {"Unit Contract": "sales_invoice", "Property Maintenance Request": "sales_invoice"})


def purchase_invoice(data=None):
	return _group(data, "Real Estate", ["Progress Claim", "Sales Commission"], {"Progress Claim": "purchase_invoice", "Sales Commission": "purchase_invoice"})


def payment_entry(data=None):
	return _group(data, "Real Estate", ["Unit Reservation", "Post Dated Cheque"], {"Unit Reservation": "deposit_entry", "Post Dated Cheque": "payment_entry"})


def project(data=None):
	return _group(data, "Real Estate", ["Real Estate Project"], {"Real Estate Project": "erp_project"})
