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
		{"fieldname": "net_salary", "label": "Net Salary", "fieldtype": "Currency", "width": 120},
		{"fieldname": "payment_date", "label": "Payment Date", "fieldtype": "Date", "width": 120},
		{"fieldname": "mode_of_payment", "label": "Payment Method", "fieldtype": "Data", "width": 120},
		{"fieldname": "reference_no", "label": "Reference No", "fieldtype": "Data", "width": 120},
		{"fieldname": "journal_entry", "label": "Accrual Entry", "fieldtype": "Link", "options": "Journal Entry", "width": 140},
		{"fieldname": "bank_entry", "label": "Payment Entry", "fieldtype": "Link", "options": "Journal Entry", "width": 140},
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
			sp.net_salary,
			sp.payment_date,
			sp.mode_of_payment,
			sp.reference_no,
			sp.journal_entry,
			sp.bank_entry
		FROM `tabSalary Payment` sp
		WHERE sp.status = 'Paid'
		{conditions}
		ORDER BY sp.payment_date DESC, sp.employee
	""", filters, as_dict=True)
	
	return data


def get_conditions(filters):
	conditions = ""
	
	if filters.get("from_date"):
		conditions += " AND sp.payment_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND sp.payment_date <= %(to_date)s"
	if filters.get("employee"):
		conditions += " AND sp.employee = %(employee)s"
	if filters.get("department"):
		conditions += " AND sp.department = %(department)s"
	if filters.get("mode_of_payment"):
		conditions += " AND sp.mode_of_payment = %(mode_of_payment)s"
	
	return conditions
