# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

"""Shared server-side utilities for Reckon HRMS.

All salary maths live here so they are always performed on the server and can be
unit-tested independently of any document.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, get_first_day, get_last_day, getdate

SETTINGS_DOCTYPE = "Reckon HRMS Settings"


def get_settings():
	"""Return the Reckon HRMS Settings singleton (creating defaults if missing)."""
	if not frappe.db.exists(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE):
		settings = frappe.get_doc({"doctype": SETTINGS_DOCTYPE, "working_days": 30}).insert(
			ignore_permissions=True, ignore_mandatory=True
		)
		return settings
	return frappe.get_cached_doc(SETTINGS_DOCTYPE)


def validate_accounting_settings(settings, mode_of_payment, company=None):
	"""Validate accounting configuration and return the target Bank/Cash account.

	Raises a clear error if the configuration is missing so the salary is never
	marked Paid without accounting.
	"""
	problems = []

	if not settings.company:
		problems.append(_("Company is not set in Reckon HRMS Settings"))
	if not settings.salary_expense_account:
		problems.append(_("Salary Expense Account is not set in Reckon HRMS Settings"))
	if not settings.salary_payable_account:
		problems.append(_("Salary Payable Account is not set in Reckon HRMS Settings"))

	account_field = "default_bank_account" if mode_of_payment == "Bank" else "default_cash_account"
	if not settings.get(account_field):
		problems.append(
			_("{0} is not set in Reckon HRMS Settings").format(
				_("Default Bank Account") if mode_of_payment == "Bank" else _("Default Cash Account")
			)
		)

	if company and settings.company and settings.company != company:
		problems.append(
			_("Salary company ({0}) does not match the configured accounting company ({1})").format(
				company, settings.company
			)
		)

	if problems:
		frappe.throw(
			"<br>".join(["• " + p for p in problems])
			+ "<br><br>"
			+ _("Ask your administrator to configure Reckon HRMS Settings → Accounting Settings."),
			title=_("Accounting Not Configured"),
		)

	target_account = settings.get(account_field)

	# make sure the accounts actually exist and belong to the configured company
	for account in (settings.salary_expense_account, settings.salary_payable_account, target_account):
		acc_company = frappe.db.get_value("Account", account, "company")
		if not acc_company:
			frappe.throw(_("Account {0} does not exist").format(account))
		if acc_company != settings.company:
			frappe.throw(
				_("Account {0} does not belong to company {1}").format(account, settings.company)
			)

	return target_account


# ---------------------------------------------------------------------- #
# Attendance
# ---------------------------------------------------------------------- #


def get_attendance_summary(employee, month_start):
	"""Aggregate standard Frappe HR Attendance records for one employee/month.

	Returns dict with keys: present, absent, half_day, late, on_leave,
	work_from_home, total_working_hours.
	"""
	month_start = getdate(get_first_day(month_start))
	month_end = getdate(get_last_day(month_start))

	rows = frappe.db.sql(
		"""
		SELECT status, late_entry, COUNT(*) AS count
		FROM tabAttendance
		WHERE employee = %s
			AND attendance_date BETWEEN %s AND %s
			AND docstatus = 1
		GROUP BY status, late_entry
		""",
		(employee, month_start, month_end),
		as_dict=True,
	)

	summary = {
		"present": 0.0,
		"absent": 0.0,
		"half_day": 0.0,
		"late": 0,
		"on_leave": 0.0,
		"work_from_home": 0.0,
	}

	for row in rows:
		count = cint(row.count)
		if row.status in ("Present", "Work From Home"):
			summary["present"] += count
			if row.status == "Work From Home":
				summary["work_from_home"] += count
		elif row.status == "Absent":
			summary["absent"] += count
		elif row.status == "Half Day":
			summary["half_day"] += count
		elif row.status == "On Leave":
			summary["on_leave"] += count
		if cint(row.late_entry) and row.status in ("Present", "Work From Home", "Half Day"):
			summary["late"] += count

	# present_days counts half days as 0.5 day (leave days are treated as paid,
	# i.e. not deducted - configure absent/half-day rules in Settings)
	return summary


# ---------------------------------------------------------------------- #
# Salary calculation (pure functions - always server-side)
# ---------------------------------------------------------------------- #


def calculate_attendance_deduction(
	gross_salary,
	working_days,
	absent_days=0,
	half_day_count=0,
	late_count=0,
	absent_deduction_per_day=1.0,
	late_count_for_deduction=3,
	half_day_deduction=0.5,
):
	"""Calculate the attendance deduction amount.

	daily_salary = gross_salary / working_days
	absent deduction = absent_days * absent_deduction_per_day * daily_salary
	late deduction = (late_count // late_count_for_deduction) * daily_salary
	half day deduction = half_day_count * half_day_deduction * daily_salary
	"""
	working_days = cint(working_days) or 30
	if working_days <= 0:
		working_days = 30

	daily_salary = flt(gross_salary) / working_days

	late_day_credits = 0
	if late_count_for_deduction and cint(late_count_for_deduction) > 0:
		late_day_credits = cint(late_count) // cint(late_count_for_deduction)

	deduction_days = (
		flt(absent_days) * flt(absent_deduction_per_day, 3)
		+ late_day_credits
		+ flt(half_day_count) * flt(half_day_deduction, 3)
	)

	return flt(deduction_days * daily_salary, 2)


def calc_net_salary(gross_salary, total_allowance=0, total_bonus=0, attendance_deduction=0, total_other_deduction=0):
	"""net = gross + allowance + bonus - attendance deduction - other deduction."""
	return flt(
		flt(gross_salary)
		+ flt(total_allowance)
		+ flt(total_bonus)
		- flt(attendance_deduction)
		- flt(total_other_deduction),
		2,
	)


def salary_row_summary(gross_salary, allowance_total=0, bonus_total=0, attendance_deduction=0, other_deduction_total=0):
	"""Calculate a full salary row - used by both Salary Payment and Bulk Salary."""
	return {
		"gross_salary": flt(gross_salary, 2),
		"allowance_total": flt(allowance_total, 2),
		"bonus_total": flt(bonus_total, 2),
		"attendance_deduction": flt(attendance_deduction, 2),
		"other_deduction_total": flt(other_deduction_total, 2),
		"net_salary": calc_net_salary(
			gross_salary, allowance_total, bonus_total, attendance_deduction, other_deduction_total
		),
	}


def get_employees_for_bulk(company, department=None, employee_type=None, grade=None):
	"""Active employees matching the bulk salary filters."""
	filters = {"status": "Active"}
	if company:
		filters["company"] = company
	if department:
		filters["department"] = department
	if employee_type:
		filters["employment_type"] = employee_type
	if grade:
		filters["grade"] = grade

	return frappe.db.get_all(
		"Employee",
		filters=filters,
		fields=["name", "employee_name", "department", "designation", "gross_salary"],
		order_by="employee_name",
	)


def month_range(month_start):
	month_start = getdate(get_first_day(month_start))
	return month_start, getdate(get_last_day(month_start))
