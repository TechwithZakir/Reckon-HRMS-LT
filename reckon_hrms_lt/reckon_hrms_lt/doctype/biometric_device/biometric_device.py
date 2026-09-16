# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class BiometricDevice(Document):
	def validate(self):
		if self.port is not None and (self.port < 1 or self.port > 65535):
			frappe.throw(_("Port must be between 1 and 65535"))

		if self.sync_interval_minutes is not None and self.sync_interval_minutes < 1:
			frappe.throw(_("Sync interval must be at least 1 minute"))

	@frappe.whitelist()
	def test_connection(self):
		"""Test connection to the biometric device."""
		from reckon_hrms_lt.biometric.manager import BiometricSyncManager

		try:
			message = BiometricSyncManager().test_device_connection(self.name)
			frappe.msgprint(message, title=_("Connection Test"), indicator="green")
			return message
		except Exception as e:
			frappe.msgprint(str(e), title=_("Connection Failed"), indicator="red")
			raise

	@frappe.whitelist()
	def sync_now(self):
		"""Trigger an immediate background sync for this device."""
		if not self.enabled:
			frappe.throw(_("Device {0} is disabled. Enable it before syncing.").format(self.device_name))

		frappe.enqueue(
			"reckon_hrms_lt.biometric.manager.sync_single_device",
			device_name=self.name,
			queue="short",
			timeout=600,
			now=frappe.flags.in_test,
		)
		frappe.msgprint(_("Sync started in the background. Check the Biometric Sync Log for results."))
