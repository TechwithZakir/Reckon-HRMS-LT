# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

"""Document-level tests for Salary Payment."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from reckon_hrms_lt.utils import calc_net_salary


class TestSalaryPayment(IntegrationTestCase):
	"""Integration tests for Salary Payment validation and accounting."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.settings = frappe.get_single("Reckon HRMS Settings")

	def test_calc_net_salary_matches_utils(self):
		result = calc_net_salary(30000, 2000, 1000, 3000, 500)
		self.assertEqual(result, 29500)

	def test_future_salary_month_blocked(self):
		from datetime import timedelta
		future_date = frappe.utils.add_months(today(), 1)

		doc = frappe.get_doc({
			"doctype": "Salary Payment",
			"employee": "_T-Employee-00001",
			"company": self.settings.company or "_Test Company",
			"salary_month": future_date,
			"gross_salary": 10000,
			"status": "Draft",
		})
		doc.flags.ignore_permissions = True

		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_negative_gross_blocked(self):
		if not frappe.db.get_value("Company", {"company_name": "_Test Company"}):
			self.skipTest("_Test Company not available")

		company = frappe.db.get_value("Company", {"company_name": "_Test Company"})
		doc = frappe.get_doc({
			"doctype": "Salary Payment",
			"employee": "_T-Employee-00001",
			"company": company,
			"salary_month": today(),
			"gross_salary": -1000,
		})
		doc.flags.ignore_permissions = True

		with self.assertRaises(frappe.ValidationError):
			doc.insert()