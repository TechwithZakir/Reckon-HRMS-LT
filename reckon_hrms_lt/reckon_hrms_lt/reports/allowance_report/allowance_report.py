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
		{"fieldname": "total_allowance", "label": "Total Allowance", "fieldtype": "Currency", "width": 140},
		{"fieldname": "total_bonus", "label": "Total Bonus", "fieldtype": "Currency", "width": 140},
		{"fieldname": "total_earnings", "label": "Total Earnings", "fieldtype": "Currency", "width": 140},
	]


def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT 
			sp.employee,
			sp.employee_name,
			sp.department,
			sp.salary_month,
			sp.total_allowance,
			sp.total_bonus,
			(sp.total_allowance + sp.total_bonus) as total_earnings
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
	
	return conditions
