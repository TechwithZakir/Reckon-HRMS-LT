# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "device", "label": "Device", "fieldtype": "Link", "options": "Biometric Device", "width": 180},
		{"fieldname": "sync_time", "label": "Sync Time", "fieldtype": "Datetime", "width": 180},
		{"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 100},
		{"fieldname": "records_processed", "label": "Records Processed", "fieldtype": "Int", "width": 140},
		{"fieldname": "successful", "label": "Successful", "fieldtype": "Int", "width": 100},
		{"fieldname": "failed", "label": "Failed", "fieldtype": "Int", "width": 80},
		{"fieldname": "error_message", "label": "Error", "fieldtype": "Small Text", "width": 300},
	]


def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT 
			bsl.device,
			bsl.sync_time,
			bsl.status,
			bsl.records_processed,
			bsl.successful,
			bsl.failed,
			bsl.error_message
		FROM `tabBiometric Sync Log` bsl
		WHERE 1=1
		{conditions}
		ORDER BY bsl.sync_time DESC
	""", filters, as_dict=True)
	
	return data


def get_conditions(filters):
	conditions = ""
	
	if filters.get("device"):
		conditions += " AND bsl.device = %(device)s"
	if filters.get("from_date"):
		conditions += " AND bsl.sync_time >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND bsl.sync_time <= %(to_date)s"
	if filters.get("status"):
		conditions += " AND bsl.status = %(status)s"
	
	return conditions
