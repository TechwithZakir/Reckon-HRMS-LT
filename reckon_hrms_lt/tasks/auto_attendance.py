# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

"""Auto attendance processing from Employee Checkin records.

Creates standard Frappe HR Attendance records from check-ins using the rules
configured in Reckon HRMS Settings. Idempotent: skips employees/dates that
already have an Attendance record. One failure never blocks other employees.
"""

from datetime import datetime, time as dtime, timedelta

import frappe
from frappe.utils import add_days, cint, flt, getdate, nowdate


def process_auto_attendance():
	"""Daily scheduled task: process yesterday's check-ins into Attendance records."""
	from reckon_hrms_lt.utils import get_settings

	try:
		settings = get_settings()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Reckon HRMS: settings not available for auto attendance")
		return

	target_date = getdate(add_days(nowdate(), -1))

	employees = frappe.get_all(
		"Employee",
		filters={
			"status": "Active",
			**(
				{"company": settings.company}
				if settings.company
				else {}
			),
		},
		pluck="name",
	)

	if not employees:
		return

	# Employees that already have attendance for the target date
	marked = set(
		frappe.get_all(
			"Attendance",
			filters={"attendance_date": target_date, "employee": ("in", employees)},
			pluck="employee",
		)
	)

	# Single query: all check-ins for the target date for these employees
	checkins = frappe.get_all(
		"Employee Checkin",
		filters=[
			["employee", "in", employees],
			["time", ">=", datetime.combine(target_date, dtime.min)],
			["time", "<", datetime.combine(add_days(target_date, 1), dtime.min)],
		],
		fields=["employee", "time", "log_type"],
		order_by="time asc",
	)

	checkins_by_employee = {}
	for row in checkins:
		checkins_by_employee.setdefault(row.employee, []).append(row)

	for employee in employees:
		if employee in marked:
			continue
		try:
			_process_employee_attendance(employee, target_date, checkins_by_employee.get(employee, []), settings)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(
				frappe.get_traceback(),
				f"Reckon HRMS: auto attendance failed for {employee} on {target_date}",
			)


def _process_employee_attendance(employee, date, employee_checkins, settings):
	"""Process attendance for a single employee on a specific date."""
	if not employee_checkins and not cint(settings.mark_absent_auto):
		return

	company = frappe.db.get_value("Employee", employee, "company")

	if not employee_checkins:
		_create_attendance_record(employee, date, "Absent", 0, company)
		return

	first_checkin = None
	last_checkout = None
	for row in employee_checkins:
		if row.log_type == "IN" and first_checkin is None:
			first_checkin = row.time
		elif row.log_type == "OUT":
			last_checkout = row.time

	first_time = first_checkin or employee_checkins[0].time
	if first_time is None:
		return

	working_hours = 0.0
	if last_checkout:
		working_hours = flt((last_checkout - first_time).total_seconds() / 3600, 2)

	late_entry = 1 if _is_late(first_time, date, settings) else 0

	status = "Present"
	half_day_hours = flt(settings.half_day_working_hours or 4)
	if 0 < working_hours < half_day_hours:
		status = "Half Day"

	_create_attendance_record(employee, date, status, working_hours, company, late_entry)


def _is_late(checkin_time, date, settings):
	"""True when the check-in is later than office start + threshold."""
	office_start = settings.office_start_time or "09:00:00"
	if isinstance(office_start, str):
		try:
			parsed = datetime.strptime(office_start, "%H:%M:%S")
		except ValueError:
			try:
				parsed = datetime.strptime(office_start, "%H:%M:%S.%f")
			except ValueError:
				return 0
		office_start = parsed.time()

	start_dt = datetime.combine(getdate(date), office_start)
	threshold_dt = start_dt + timedelta(minutes=cint(settings.late_threshold_minutes or 15))
	return checkin_time > threshold_dt


def _create_attendance_record(employee, date, status, working_hours, company, late_entry=0):
	"""Create and submit a standard Frappe HR Attendance record."""
	attendance = frappe.get_doc({
		"doctype": "Attendance",
		"naming_series": "HR-ATT-.YYYY.-",
		"employee": employee,
		"attendance_date": date,
		"status": status,
		"late_entry": late_entry,
		"working_hours": flt(working_hours, 2),
		"company": company,
	})
	attendance.flags.ignore_duplicate_check = True
	attendance.flags.ignore_permissions = True
	attendance.insert()
	attendance.submit()
