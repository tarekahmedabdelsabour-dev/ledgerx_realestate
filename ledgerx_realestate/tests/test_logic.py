"""Pure-logic tests: python3 -m unittest discover -s ledgerx_realestate/tests (no site needed)."""
import importlib.util
import os
import unittest

_p = os.path.join(os.path.dirname(__file__), "..", "engine", "logic.py")
_s = importlib.util.spec_from_file_location("realestate_logic", _p)
L = importlib.util.module_from_spec(_s)
_s.loader.exec_module(L)


class T(unittest.TestCase):
	def test_price_and_totals(self):
		self.assertEqual(L.unit_price(150, 40, 20000, 8000, 5), 3486000)
		t = L.contract_totals(3000000, 100000, 10, 0, 2)
		self.assertEqual((t["net"], t["markup"], t["price"], t["deposit"], t["total"]), (2900000, 290000, 3190000, 63800, 3253800))
		self.assertEqual(L.contract_totals(1000, 0, 0, 14, 0)["total"], 1140)
		with self.assertRaises(ValueError):
			L.contract_totals(100, 200)

	def test_schedule_adds_up(self):
		rows = L.plan_schedule(3253800, "2026-12-01", 10, 36, 3, [(5, 12)], 0, None, [(63800, "2028-06-30", "Maintenance Deposit")], 3)
		self.assertEqual(round(sum(a for _d, a, _l in rows), 2), 3253800)
		labels = [l for _d, _a, l in rows]
		self.assertEqual(labels.count("Installment"), 36)
		self.assertEqual(rows[0][2], "Down Payment")
		self.assertEqual(str(rows[0][0]), "2026-12-01")
		self.assertIn("Maintenance Deposit", labels)
		self.assertEqual(sorted(r[0] for r in rows), [r[0] for r in rows])

	def test_schedule_edges(self):
		rows = L.plan_schedule(100, "2026-01-31", 0, 3, 1)
		self.assertEqual([str(r[0]) for r in rows], ["2026-02-28", "2026-03-31", "2026-04-30"])
		self.assertEqual(round(sum(r[1] for r in rows), 2), 100)
		rows = L.plan_schedule(1000, "2026-01-01", 100)
		self.assertEqual(rows, [(L._d("2026-01-01"), 1000.0, "Down Payment")])
		with self.assertRaises(ValueError):
			L.plan_schedule(1000, "2026-01-01", 60, 1, 1, [(50, 6)])
		with self.assertRaises(ValueError):
			L.plan_schedule(1000, "2026-01-01", 10, 1, 1, [], 10, None)

	def test_commission(self):
		self.assertEqual(L.commission(3000000, 2.5), 75000)
		self.assertTrue(L.commission_due(300000, 3000000, 10))
		self.assertFalse(L.commission_due(299999, 3000000, 10))
		self.assertEqual(L.late_fee(100000, 2, 1.5), 3000)
		self.assertEqual(L.late_fee(100000, -1, 1.5), 0)

	def test_progress_claim(self):
		c = L.progress_claim(10000000, 30, 1000000, 10, 20, 500000, 25000)
		self.assertEqual((c["cumulative"], c["gross"], c["retention"], c["advance"], c["net"]), (3000000, 2000000, 200000, 400000, 1375000))
		c = L.progress_claim(1000, 50, 0, 0, 50, 100, 0)
		self.assertEqual((c["advance"], c["net"]), (100, 400))
		with self.assertRaises(ValueError):
			L.progress_claim(1000, 10, 500)

	def test_rent(self):
		self.assertEqual(L.rent_for_period(10000, 10, "2026-01-15", "2026-12-15"), 10000)
		self.assertEqual(L.rent_for_period(10000, 10, "2026-01-15", "2027-01-15"), 11000)
		self.assertEqual(L.rent_for_period(10000, 10, "2026-01-15", "2028-02-15"), 12100)
		ps = L.rental_periods("2026-01-15", "2026-12-31", None, "2026-03-20")
		self.assertEqual([str(p) for p in ps], ["2026-01-15", "2026-02-15", "2026-03-15"])
		ps = L.rental_periods("2026-01-15", "2026-12-31", "2026-03-15", "2026-05-01")
		self.assertEqual([str(p) for p in ps], ["2026-04-15"])
		self.assertEqual(L.rental_periods("2026-01-15", "2026-02-20", "2026-02-15", "2026-09-01"), [])

	def test_service_and_months(self):
		self.assertEqual(L.service_charge(150, 4, 100), 700)
		self.assertEqual(L.months_between("2026-01-31", "2026-03-01"), 1)


if __name__ == "__main__":
	unittest.main()
