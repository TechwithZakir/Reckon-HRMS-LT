# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

"""Install and setup script for Reckon HRMS app."""

import frappe
from frappe import _

SETTINGS_DOCTYPE = "Reckon HRMS Settings"


def after_install():
	"""Run tasks after installing the app (idempotent)."""
	if not frappe.db.exists("Role", "HR User"):
		frappe.get_doc({"doctype": "Role", "role_name": "HR User"}).insert(
			ignore_permissions=True, ignore_if_duplicate=True
		)

	create_custom_fields()
	create_default_settings()


def create_custom_fields():
	"""Create custom fields for Employee (gross_salary).

	Idempotent: only creates if the field does not exist.
	Frappe expects Currency options to be a field name containing the currency.
	Leaving options empty uses the company default currency.
	"""
	if frappe.db.exists("Custom Field", "Employee-gross_salary"):
		return

	frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Employee",
		"label": "Gross Salary",
		"fieldname": "gross_salary",
		"fieldtype": "Currency",
		"insert_after": "date_of_joining",
		"description": "Default gross salary for the employee",
		"translatable": 0,
		"hidden": 0,
		"read_only": 0,
	}).insert(ignore_permissions=True)


def create_default_settings():
	"""Create Reckon HRMS Settings singleton with default values.

	Idempotent: only creates if the settings document does not exist.
	Upgrading or migrating does not overwrite user-customized values.
	"""
	if frappe.db.exists(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE):
		return

	frappe.get_doc({
		"doctype": SETTINGS_DOCTYPE,
		"working_days": 30,
		"late_threshold_minutes": 15,
		"late_count_for_deduction": 3,
		"absent_deduction_per_day": 1,
		"half_day_deduction": 0.5,
		"office_start_time": "09:00:00",
		"half_day_working_hours": 4,
	}).insert(ignore_permissions=True)


def after_migrate():
	"""Run tasks after migrations (idempotent and non-destructive)."""
	if not frappe.db.exists("Custom Field", "Employee-gross_salary"):
		create_custom_fields()

	if not frappe.db.exists(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE):
		create_default_settings()