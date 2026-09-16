# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "width": 150},
		{"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 180},
		{"fieldname": "attendance_date", "label": "Date", "fieldtype": "Date", "width": 120},
		{"fieldname": "check_in", "label": "Check In", "fieldtype": "Time", "width": 100},
		{"fieldname": "check_out", "label": "Check Out", "fieldtype": "Time", "width": 100},
		{"fieldname": "working_hours", "label": "Working Hours", "fieldtype": "Float", "width": 100},
		{"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 100},
	]


def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT 
			a.employee,
			a.employee_name,
			a.attendance_date,
			MIN(ec.time) as check_in,
			MAX(ec.time) as check_out,
			a.total_working_hours as working_hours,
			a.status
		FROM `tabAttendance` a
		LEFT JOIN `tabEmployee Checkin` ec ON ec.employee = a.employee 
			AND DATE(ec.time) = a.attendance_date
		WHERE a.docstatus = 1
		{conditions}
		GROUP BY a.name, a.employee, a.employee_name, a.attendance_date, a.total_working_hours, a.status
		ORDER BY a.attendance_date DESC, a.employee
	""", filters, as_dict=True)
	
	return data


def get_conditions(filters):
	conditions = ""
	
	if filters.get("from_date"):
		conditions += " AND a.attendance_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND a.attendance_date <= %(to_date)s"
	if filters.get("employee"):
		conditions += " AND a.employee = %(employee)s"
	if filters.get("department"):
		conditions += """ AND a.employee IN (
			SELECT name FROM `tabEmployee` WHERE department = %(department)s
		)"""
	if filters.get("status"):
		conditions += " AND a.status = %(status)s"
	
	return conditions
