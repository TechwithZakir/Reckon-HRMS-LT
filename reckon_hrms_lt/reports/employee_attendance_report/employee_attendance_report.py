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
		{"fieldname": "present_days", "label": "Present Days", "fieldtype": "Float", "width": 100},
		{"fieldname": "absent_days", "label": "Absent Days", "fieldtype": "Float", "width": 100},
		{"fieldname": "half_day_days", "label": "Half Days", "fieldtype": "Float", "width": 100},
		{"fieldname": "late_count", "label": "Late Count", "fieldtype": "Int", "width": 100},
		{"fieldname": "leave_days", "label": "Leave Days", "fieldtype": "Float", "width": 100},
		{"fieldname": "total_working_hours", "label": "Total Hours", "fieldtype": "Float", "width": 100},
	]


def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT 
			a.employee,
			a.employee_name,
			e.department,
			SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_days,
			SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_days,
			SUM(CASE WHEN a.status = 'Half Day' THEN 1 ELSE 0 END) as half_day_days,
			SUM(CASE WHEN a.late_entry = 1 THEN 1 ELSE 0 END) as late_count,
			SUM(CASE WHEN a.status = 'On Leave' THEN 1 ELSE 0 END) as leave_days,
			SUM(a.total_working_hours) as total_working_hours
		FROM `tabAttendance` a
		LEFT JOIN `tabEmployee` e ON e.name = a.employee
		WHERE a.docstatus = 1
		{conditions}
		GROUP BY a.employee, a.employee_name, e.department
		ORDER BY a.employee
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
