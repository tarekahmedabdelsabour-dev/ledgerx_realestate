"""Pure calculations (no database), so they can be tested without a site."""
import calendar
from datetime import date, datetime


def r2(x):
	return round(float(x or 0) + 1e-9, 2)


def _d(v):
	if isinstance(v, datetime):
		return v.date()
	if isinstance(v, date):
		return v
	return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()


def add_months(d, n):
	d = _d(d)
	m = d.month - 1 + int(n)
	y, m = d.year + m // 12, m % 12 + 1
	return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def months_between(a, b):
	a, b = _d(a), _d(b)
	return (b.year - a.year) * 12 + b.month - a.month - (1 if b.day < a.day else 0)


def unit_price(area_built, area_garden, per_m2, garden_per_m2, premium_pct=0):
	base = float(area_built or 0) * float(per_m2 or 0) + float(area_garden or 0) * float(garden_per_m2 or 0)
	return r2(base * (1 + float(premium_pct or 0) / 100))


def contract_totals(list_price, discount=0, markup_pct=0, vat_rate=0, deposit_pct=0):
	"""markup_pct: extra charged by a long payment plan. The maintenance deposit is held for the owners and is not revenue."""
	net = r2(float(list_price or 0) - float(discount or 0))
	if net < 0:
		raise ValueError("discount above the price")
	markup = r2(net * float(markup_pct or 0) / 100)
	price = r2(net + markup)
	deposit = r2(price * float(deposit_pct or 0) / 100)
	vat = r2(price * float(vat_rate or 0) / 100)
	return {"net": net, "markup": markup, "price": price, "deposit": deposit, "vat": vat, "total": r2(price + deposit + vat)}


def plan_schedule(total, contract_date, down_pct=0, count=1, interval_months=1, balloons=(), delivery_pct=0, delivery_date=None,
		fixed=(), first_after=None):
	"""Rows (date, amount, label) adding up to `total`.
	fixed: amounts due on a date that come off the top (maintenance deposit at delivery).
	down payment and balloons and delivery are percentages of what is left; the rest is split in equal installments."""
	total = r2(total)
	rows = [(_d(d), r2(a), lbl) for a, d, lbl in fixed]
	left = r2(total - sum(a for _d_, a, _l in rows))
	if left < -0.005:
		raise ValueError("fixed payments above the total")
	pcts = float(down_pct or 0) + float(delivery_pct or 0) + sum(float(p) for p, _m in balloons)
	if pcts > 100 + 1e-9:
		raise ValueError("percentages above 100")
	if float(delivery_pct or 0) and not delivery_date:
		raise ValueError("delivery date needed")
	part = lambda p: r2(left * float(p) / 100)
	if down_pct:
		rows.append((_d(contract_date), part(down_pct), "Down Payment"))
	for p, m in balloons:
		rows.append((add_months(contract_date, m), part(p), "Extra Payment"))
	if delivery_pct:
		rows.append((_d(delivery_date), part(delivery_pct), "Delivery"))
	rest = r2(total - sum(a for _d_, a, _l in rows))
	count = max(int(count or 1), 1)
	if rest > 0.004:
		each = r2(rest / count)
		start = int(first_after if first_after is not None else interval_months or 1)
		for i in range(count):
			amount = each if i < count - 1 else r2(rest - each * (count - 1))
			rows.append((add_months(contract_date, start + i * int(interval_months or 1)), amount, "Installment"))
	elif rest < -0.004:
		raise ValueError("schedule above the total")
	rows.sort(key=lambda r: (r[0], r[2] != "Down Payment"))
	diff = r2(total - sum(a for _d_, a, _l in rows))
	if abs(diff) > 0.004 and rows:
		d, a, l = rows[-1]
		rows[-1] = (d, r2(a + diff), l)
	return rows


def commission(base, pct):
	return r2(float(base or 0) * float(pct or 0) / 100)


def commission_due(collected, total, threshold_pct):
	"""A broker is paid once the customer has paid at least threshold_pct of the contract."""
	return float(total or 0) > 0 and float(collected or 0) * 100 >= float(total) * float(threshold_pct or 0) - 1e-9


def late_fee(overdue, months_late, pct_per_month):
	return r2(float(overdue or 0) * max(int(months_late or 0), 0) * float(pct_per_month or 0) / 100)


def progress_claim(contract_value, cumulative_pct, previous_gross, retention_pct=0, advance_pct=0, advance_left=None, penalties=0):
	"""A contractor's claim: the work done to date less what was already claimed, less retention, advance recovery and penalties."""
	cumulative = r2(float(contract_value or 0) * min(max(float(cumulative_pct or 0), 0), 100) / 100)
	gross = r2(cumulative - float(previous_gross or 0))
	if gross < 0:
		raise ValueError("progress lower than the previous claim")
	retention = r2(gross * float(retention_pct or 0) / 100)
	advance = r2(gross * float(advance_pct or 0) / 100)
	if advance_left is not None:
		advance = min(advance, r2(advance_left))
	net = r2(gross - retention - advance - float(penalties or 0))
	return {"cumulative": cumulative, "gross": gross, "retention": retention, "advance": advance, "net": net}


def rent_for_period(rent, increase_pct, start, period_start):
	"""The monthly rent grows by increase_pct at every anniversary of the start date."""
	years = max(months_between(start, period_start) // 12, 0)
	return r2(float(rent) * (1 + float(increase_pct or 0) / 100) ** years)


def rental_periods(start, end, last_billed, today):
	"""First days of the months that are due to be billed: from the month after the last billed one, up to today."""
	start, end, today = _d(start), _d(end), _d(today)
	cur = add_months(date(start.year, start.month, 1), 0) if not last_billed else add_months(_d(last_billed), 1)
	cur = date(cur.year, cur.month, start.day if not last_billed else cur.day)
	out = []
	while cur <= today and cur <= end:
		out.append(cur)
		cur = add_months(cur, 1)
	return out


def service_charge(area, rate_per_m2, fixed=0):
	return r2(float(area or 0) * float(rate_per_m2 or 0) + float(fixed or 0))
