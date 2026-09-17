# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

from . import __version__ as app_version

app_name = "reckon_hrms_lt"
app_title = "Reckon HRMS"
app_publisher = "Reckon Technologies Ltd."
app_description = "Simple HRMS application for Frappe/ERPNext v16"
app_email = "hello@reckon.tech"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/reckon_hrms_lt/css/reckon_hrms_lt.css"
# app_include_js = "/assets/reckon_hrms_lt/js/reckon_hrms_lt.js"

# include js, css files in header of web template
# web_include_css = "/assets/reckon_hrms_lt/css/web.css"
# web_include_js = "/assets/reckon_hrms_lt/js/web.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "reckon_hrms_lt/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record type
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "reckon_hrms_lt.utils.jinja_methods",
#	"filters": "reckon_hrms_lt.utils.jinja_filters"
# }

# Installation
# ------------

after_install = "reckon_hrms_lt.install.after_install"
after_migrate = "reckon_hrms_lt.install.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "reckon_hrms_lt.uninstall.before_uninstall"
# after_uninstall = "reckon_hrms_lt.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up integration with other apps or platforms
# integration_setup = {
#	"integration_name": {
#		"setup_functions": {
#			"setup": "reckon_hrms_lt.integrations.integration_name.setup",
#			"teardown": "reckon_hrms_lt.integrations.integration_name.teardown",
#		}
#	}
# }

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "reckon_hrms_lt.notifications.get_notification_config"

# Permissions
# -----------
# in this app, permissions are managed through DocTypes and Roles

# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Employee Checkin": {
		"validate": "reckon_hrms_lt.doc_events.validate_duplicate_checkin"
	},
	"Attendance": {
		"validate": "reckon_hrms_lt.doc_events.validate_duplicate_attendance"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"reckon_hrms_lt.tasks.biometric_sync.sync_biometric_devices"
	],
	"daily": [
		"reckon_hrms_lt.tasks.auto_attendance.process_auto_attendance"
	]
}

# Testing
# -------

# before_tests = "reckon_hrms_lt.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "reckon_hrms_lt.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the above endpoints.
# data = frappe._dict(defaults={
# 	"posting_date": today(),
# 	"company": None,
# }, **kwargs)

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"reckon_hrms_lt.auth.validate"
# ]

# Reports
# -------

# The reports are loaded via their JSON definition files in the reports/ folder.
# No additional hook is required for Script Reports.
