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
		{"fieldname": "salary_month", "label": "Month", "fieldtype": "Date", "width": 120},
		{"fieldname": "gross_salary", "label": "Gross Salary", "fieldtype": "Currency", "width": 120},
		{"fieldname": "total_allowance", "label": "Allowance", "fieldtype": "Currency", "width": 100},
		{"fieldname": "total_bonus", "label": "Bonus", "fieldtype": "Currency", "width": 100},
		{"fieldname": "attendance_deduction", "label": "Att. Deduction", "fieldtype": "Currency", "width": 120},
		{"fieldname": "total_other_deduction", "label": "Other Deduction", "fieldtype": "Currency", "width": 120},
		{"fieldname": "net_salary", "label": "Net Salary", "fieldtype": "Currency", "width": 120},
		{"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 100},
		{"fieldname": "payment_date", "label": "Payment Date", "fieldtype": "Date", "width": 120},
	]


def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT 
			sp.employee,
			sp.employee_name,
			sp.department,
			sp.salary_month,
			sp.gross_salary,
			sp.total_allowance,
			sp.total_bonus,
			sp.attendance_deduction,
			sp.total_other_deduction,
			sp.net_salary,
			sp.status,
			sp.payment_date
		FROM `tabSalary Payment` sp
		WHERE 1=1
		{conditions}
		ORDER BY sp.salary_month DESC, sp.employee
	""", filters, as_dict=True)
	
	return data


def get_conditions(filters):
	conditions = ""
	
	if filters.get("salary_month"):
		conditions += " AND sp.salary_month = %(salary_month)s"
	if filters.get("employee"):
		conditions += " AND sp.employee = %(employee)s"
	if filters.get("department"):
		conditions += " AND sp.department = %(department)s"
	if filters.get("status"):
		conditions += " AND sp.status = %(status)s"
	
	return conditions
