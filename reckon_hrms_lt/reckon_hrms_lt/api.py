# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

"""Public API endpoints for Reckon HRMS."""

import frappe
from frappe import _
from frappe.utils import today

from reckon_hrms_lt.utils import get_settings


def get_default_gross_salary(employee):
	"""Return the default gross salary configured on the Employee (custom field)."""
	return frappe.utils.flt(frappe.db.get_value("Employee", employee, "gross_salary") or 0, 2)


def pay_salary_payments(names):
	"""Pay multiple Salary Payment records (used by Bulk Salary). Runs each independently."""
	import json

	if isinstance(names, str):
		names = json.loads(names)

	results = {"paid": [], "failed": []}
	for name in names:
		doc = frappe.get_doc("Salary Payment", name)
		try:
			if doc.status != "Paid":
				doc.pay_salary()
				results["paid"].append(name)
		except Exception:
			results["failed"].append({"name": name, "error": frappe.get_traceback()})
			frappe.log_error(frappe.get_traceback(), f"Bulk salary payment failed for {name}")

	return results


def get_erpnext_company_currencies():
	"""Return all company currencies for use in multi-company environments."""
	return frappe.db.sql(
		"SELECT name, default_currency FROM tabCompany",
		as_dict=True,
	)


def validate_company_currency(company, currency):
	"""Validate that the company's default currency matches the expected currency."""
	if not company:
		return False

	company_currency = frappe.db.get_value("Company", company, "default_currency")
	return company_currency == currency


def get_company_accounting_settings(company):
	"""Retrieve accounting settings for the given company."""
	settings = get_settings()
	if settings.company != company:
		return None

	return {
		"salary_expense_account": settings.salary_expense_account,
		"salary_payable_account": settings.salary_payable_account,
		"default_bank_account": settings.default_bank_account,
		"default_cash_account": settings.default_cash_account,
		"cost_center": settings.cost_center,
	}
