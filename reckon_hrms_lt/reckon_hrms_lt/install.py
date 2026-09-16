# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

"""Install and setup script for Reckon HRMS app."""

import frappe
from frappe import _

SETTINGS_DOCTYPE = "Reckon HRMS Settings"


def after_install():
	"""Run tasks after installing the app."""
	try:
		create_custom_fields()
		create_default_settings()
		create_roles()
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Reckon HRMS Install Failed")
		raise


def create_custom_fields():
	"""Create custom fields for Employee (gross_salary)."""
	if not frappe.db.exists("Custom Field", "Employee-gross_salary"):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Employee",
			"label": "Gross Salary",
			"fieldname": "gross_salary",
			"fieldtype": "Currency",
			"insert_after": "status",
			"options": "Company",  # links to company currency
			"description": "Default gross salary for the employee",
			"translatable": 0,
		}).insert(ignore_permissions=True)

	# Also ensure the field appears on the Employee form
	employee_form = frappe.get_doc("Customize Form", "Employee")
	gross_field = next(
		(field for field in employee_form.fields if field.fieldname == "gross_salary"), None
	)
	if gross_field:
		employee_form.set_value("hidden", 0)
		employee_form.save()


def create_default_settings():
	"""Create Reckon HRMS Settings singleton with default values."""
	if not frappe.db.exists(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE):
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


def create_roles():
	"""Create app-specific roles."""
	for role in ["HR User"]:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)

	# Assign permissions to HR User
	frappe.get_doc({
		"doctype": "Role Permission for Page and Report",
		"role": "HR User",
		"report": "Attendance Report",
		"read": 1
	}).insert(ignore_permissions=True)
	# Add other permissions here for HR User


def after_migrate():
	"""Run tasks after migrations."""
	after_install()
