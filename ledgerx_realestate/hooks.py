app_name = "ledgerx_realestate"
app_title = "Real Estate"
app_publisher = "LedgerX"
app_description = "Real estate development: projects, units, pricing, reservations, contracts and installments, brokers, construction and contractors, handover, maintenance, owners association, rentals"
app_email = "hello@ledgerx.local"
app_license = "mit"

required_apps = ["erpnext", "hrms", "ledgerx"]

add_to_apps_screen = [
	{
		"name": "ledgerx_realestate",
		"logo": "/assets/ledgerx_realestate/images/realestate.svg",
		"title": "Real Estate",
		"route": "/desk/real-estate",
		"has_permission": "ledgerx_realestate.install.check_app_permission",
	}
]

override_doctype_dashboards = {
	"Customer": "ledgerx_realestate.overrides.customer",
	"Supplier": "ledgerx_realestate.overrides.supplier",
	"Employee": "ledgerx_realestate.overrides.employee",
	"Sales Invoice": "ledgerx_realestate.overrides.sales_invoice",
	"Purchase Invoice": "ledgerx_realestate.overrides.purchase_invoice",
	"Payment Entry": "ledgerx_realestate.overrides.payment_entry",
	"Project": "ledgerx_realestate.overrides.project",
}

scheduler_events = {
	"cron": {
		"0 6 * * *": ["ledgerx_realestate.tasks.daily"],
		"0 5 1 * *": ["ledgerx_realestate.tasks.charge_late_fees"],
	},
}

after_install = "ledgerx_realestate.install.after_install"
after_migrate = "ledgerx_realestate.install.after_migrate"
