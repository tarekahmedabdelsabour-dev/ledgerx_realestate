# Install

```
cd ~/frappe-bench-v16/apps
git clone https://github.com/tarekahmedabdelsabour-dev/ledgerx_realestate ledgerx_realestate
cd ~/frappe-bench-v16
echo "" >> sites/apps.txt && echo "ledgerx_realestate" >> sites/apps.txt
./env/bin/pip install -e apps/ledgerx_realestate
ln -sfn ~/frappe-bench-v16/apps/ledgerx_realestate/ledgerx_realestate/public sites/assets/ledgerx_realestate
bench --site mysite.localhost install-app ledgerx_realestate
bench --site mysite.localhost migrate && bench --site mysite.localhost clear-cache
```
Then restart the server.

## First setup (Real Estate workspace)
1. **Real Estate Settings:** company and the accounts: unit sales income, maintenance deposit (a liability), late fee income, commission expense, construction cost, retention payable, rental income, service charge income, maintenance income; VAT; commission and late-fee rules.
2. **Real Estate Project** (needs a cost center: the project's profit and loss), then **Phase**, **Building**, **Unit Type**, **Property Unit** (single or many).
3. **Unit Price List** (price per m² by unit type) then *Apply to Available Units*; a unit can carry its own premium (floor, view, corner).
4. **Payment Plan:** down payment, installments, interval, extra yearly payments, payment at delivery, plan price increase, maintenance deposit.
5. Sell: **Unit Reservation** (deposit) then **Unit Contract** (picks the plan and builds the schedule) then *Confirm*: one Sales Invoice with the payment schedule, the reservation deposit applied.
6. Collect: *Receive Payment*, or **Post Dated Cheque** (deposit, cleared, bounced). Late fees are charged monthly if the setting is above 0.
7. **Real Estate Broker** (creates a supplier) and **Sales Commission**: due when the customer has paid the percent set in the settings; paid as a purchase invoice (broker) or an additional salary (salesman).
8. Build: **Bill of Quantities**, **Construction Contract** (contractor = Supplier, retention %, advance %), advance payment, **Progress Claim** (posts a purchase invoice with retention deducted and the advance set against it), **Construction Progress**.
9. After the sale: **Unit Handover** (checklist, defects, meters; starts the warranty), **Maintenance Request**, **Owners Association** + **Association Fee Run** (service charge invoices to the owners), **Rental Contract** (monthly invoices, yearly increase).
10. Roles are created automatically: Real Estate Manager, Sales, Engineer, Accountant.

## How it is tied to the rest of the app
- Contracts, rents, service charges, penalties and maintenance are Sales Invoices; deposits and receipts are Payment Entries.
- Contractor claims and broker commissions are Purchase Invoices to Suppliers; salesmen commission goes to payroll (HR Additional Salary).
- Each project has a cost center (profit and loss) and a Project record for tasks and expenses.
- The Customer, Supplier, Employee, invoices, Payment Entry and Project forms show the related real estate records.

## Known limits
- The contract invoice is fixed once submitted: rescheduling means cancelling and re-issuing the contract.
- Contract cancellation (credit note + penalty + refund) is the most complex posting here: try it on a test company first.
- Revenue is recognised when the contract is invoiced, not by construction progress.
- Advances (reservation deposit, contractor advance) are applied by customer or supplier, so unrelated advances may be used.
- Assignment of a contract to another customer and management of properties owned by third parties are not included.
- Untested on a live site: only the calculations (price, schedule, commission, claims, rent) have automated tests.
