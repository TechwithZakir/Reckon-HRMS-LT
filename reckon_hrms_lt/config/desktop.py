# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

from frappe import _


def get_data():
	return [
		{
			"module_name": "Reckon HRMS",
			"type": "module",
			"label": _("Reckon HRMS"),
			"icon": "octicon octicon-file-directory",
			"color": "#3498db",
			"description": "Simple HRMS application for Frappe/ERPNext v16",
		}
	]