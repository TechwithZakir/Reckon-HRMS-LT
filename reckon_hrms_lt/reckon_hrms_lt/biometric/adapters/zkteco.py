# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

import frappe
from datetime import datetime
from typing import List

from reckon_hrms_lt.biometric.adapters.base import BiometricAdapter, CheckinRecord


class ZKTecoAdapter(BiometricAdapter):
	"""ZKTeco biometric device adapter (implementation to be added later)"""
	
	def __init__(self, device_config):
		self.device_config = device_config
		self.connection = None
	
	def test_connection(self) -> bool:
		"""Test connection to ZKTeco device - placeholder implementation"""
		# This will be implemented later when ZKTeco integration is added
		frappe.msgprint("ZKTeco adapter: Test connection not implemented yet")
		return True
	
	def fetch_checkins(self, since: datetime) -> List[CheckinRecord]:
		"""Fetch check-in records from ZKTeco device - placeholder implementation"""
		# This will be implemented later when ZKTeco integration is added
		frappe.msgprint("ZKTeco adapter: Fetch checkins not implemented yet")
		return []
	
	def disconnect(self):
		"""Disconnect from ZKTeco device"""
		if self.connection:
			# Close connection logic will be added later
			self.connection = None
