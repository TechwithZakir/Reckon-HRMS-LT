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
		{"fieldname": "department", "label": "Department", "fieldtype": "Link", "options": "Department", "width": 120},
		{"fieldname": "attendance_date", "label": "Date", "fieldtype": "Date", "width": 120},
		{"fieldname": "check_in", "label": "Check In", "fieldtype": "Time", "width": 100},
		{"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 100},
	]


def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT 
			a.employee,
			a.employee_name,
			e.department,
			a.attendance_date,
			MIN(ec.time) as check_in,
			a.status
		FROM `tabAttendance` a
		LEFT JOIN `tabEmployee` e ON e.name = a.employee
		LEFT JOIN `tabEmployee Checkin` ec ON ec.employee = a.employee 
			AND DATE(ec.time) = a.attendance_date
		WHERE a.docstatus = 1
			AND a.late_entry = 1
		{conditions}
		GROUP BY a.name, a.employee, a.employee_name, e.department, a.attendance_date, a.status
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
		conditions += " AND e.department = %(department)s"
	
	return conditions
