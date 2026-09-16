# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

"""Auto attendance processing from Employee Checkin records."""

import frappe
from frappe import _
from frappe.utils import getdate, today, add_days, flt


def process_auto_attendance():
	"""Daily scheduled task: Process yesterday's checkins into Attendance records.
	
	This runs once daily and creates Attendance records based on Employee Checkin
	data, applying the rules configured in Reckon HRMS Settings.
	"""
	settings = frappe.get_single("Reckon HRMS Settings")
	yesterday = add_days(today(), -1)
	
	companies = frappe.get_all("Company", pluck="name")
	
	for company in companies:
		employees = frappe.get_all(
			"Employee",
			filters={"company": company, "status": "Active"},
			pluck="name"
		)
		
		for employee in employees:
			try:
				process_employee_attendance(employee, yesterday, settings)
			except Exception:
				frappe.log_error(
					frappe.get_traceback(),
					f"Auto attendance failed for {employee} on {yesterday}"
				)


def process_employee_attendance(employee, date, settings):
	"""Process attendance for a single employee on a specific date."""
	date = getdate(date)
	
	# Skip if attendance already exists
	if frappe.db.exists("Attendance", {
		"employee": employee,
		"attendance_date": date,
		"docstatus": ("<", 2)
	}):
		return
	
	# Get checkins for this employee and date
	checkins = frappe.get_all(
		"Employee Checkin",
		filters={
			"employee": employee,
			"time": ["between", [date, add_days(date, 1)]]
		},
		fields=["time", "log_type"],
		order_by="time"
	)
	
	if not checkins:
		# No checkins - mark absent only if auto-mark is enabled
		if settings.mark_absent_auto:
			create_attendance_record(employee, date, "Absent", 0, settings)
		return
	
	# Calculate working hours
	first_checkin = None
	last_checkout = None
	
	for checkin in checkins:
		if checkin.log_type == "IN" and not first_checkin:
			first_checkin = checkin.time
		elif checkin.log_type == "OUT":
			last_checkout = checkin.time
	
	if not first_checkin:
		return
	
	# Calculate working hours
	if last_checkout:
		working_hours = (last_checkout - first_checkin).total_seconds() / 3600
	else:
		working_hours = 0
	
	# Determine status
	office_start_time = parse_time(settings.office_start_time or "09:00:00")
	late_threshold = settings.late_threshold_minutes or 15
	half_day_hours = settings.half_day_working_hours or 4
	
	status = "Present"
	late_entry = 0
	
	# Check if late
	if first_checkin:
		checkin_time = first_checkin.time()
		threshold_time = office_start_time.replace(
			hour=office_start_time.hour,
			minute=office_start_time.minute + late_threshold
		)
		if checkin_time > threshold_time:
			late_entry = 1
	
	# Check half day
	if working_hours < half_day_hours and working_hours > 0:
		status = "Half Day"
	
	create_attendance_record(employee, date, status, working_hours, settings, late_entry)


def create_attendance_record(employee, date, status, working_hours, settings, late_entry=0):
	"""Create an Attendance record."""
	attendance = frappe.get_doc({
		"doctype": "Attendance",
		"employee": employee,
		"attendance_date": date,
		"status": status,
		"late_entry": late_entry,
		"total_working_hours": flt(working_hours, 2),
		"company": frappe.db.get_value("Employee", employee, "company")
	})
	attendance.flags.ignore_duplicate_check = True
	attendance.insert(ignore_permissions=True)
	attendance.submit()


def parse_time(time_str):
	"""Parse time string to datetime.time object."""
	from datetime import datetime
	return datetime.strptime(time_str, "%H:%M:%S").time()
