# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

"""Document event hooks. These extend (never modify) standard Frappe HR behaviour."""

import frappe
from frappe import _
from frappe.utils import get_datetime


def validate_duplicate_checkin(doc, method=None):
	"""Prevent duplicate Employee Checkin records (same employee, time and log type).

	Covers manual entry. Frappe HR core is not modified -
	this runs through the standard doc_events hook.
	"""
	if doc.flags.ignore_duplicate_check:
		return

	filters = {
		"employee": doc.employee,
		"time": get_datetime(doc.time),
		"name": ("!=", doc.name or ""),
	}
	if doc.log_type:
		filters["log_type"] = doc.log_type

	if frappe.db.exists("Employee Checkin", filters):
		frappe.throw(
			_("A check-in record already exists for {0} at {1} ({2})").format(
				doc.employee_name or doc.employee, doc.time, doc.log_type or ""
			),
			title=_("Duplicate Check-in"),
		)


def validate_duplicate_attendance(doc, method=None):
	"""Prevent duplicate Attendance records for the same employee and date.

	Complements Frappe HR's own duplicate handling; enforced here as well so
	manual attendance screens and imports cannot create duplicates.
	"""
	if doc.flags.ignore_duplicate_check:
		return

	existing = frappe.db.get_value(
		"Attendance",
		{
			"employee": doc.employee,
			"attendance_date": doc.attendance_date,
			"docstatus": ("<", 2),
			"name": ("!=", doc.name or ""),
		},
		["name", "docstatus"],
		as_dict=True,
	)

	if existing:
		frappe.throw(
			_("Attendance for {0} on {1} already exists: {2}").format(
				doc.employee_name or doc.employee, doc.attendance_date, existing.name
			),
			title=_("Duplicate Attendance"),
		)