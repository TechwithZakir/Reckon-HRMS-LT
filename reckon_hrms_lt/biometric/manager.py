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
from typing import Dict, Any

from reckon_hrms_lt.biometric.adapters.base import BiometricAdapter, CheckinRecord
from reckon_hrms_lt.biometric.adapters.zkteco import ZKTecoAdapter


class BiometricSyncManager:
	"""Manages biometric device synchronization"""
	
	def __init__(self):
		self.adapters: Dict[str, BiometricAdapter] = {}
	
	def get_adapter(self, device_type: str, device_config: Dict[str, Any]) -> BiometricAdapter:
		"""Get appropriate adapter for device type"""
		if device_type == "ZKTeco":
			return ZKTecoAdapter(device_config)
		else:
			# Generic adapter for other devices
			frappe.throw(f"Adapter for device type {device_type} not implemented")
	
	def test_device_connection(self, device_name: str) -> str:
		"""Test connection to a specific device"""
		device = frappe.get_doc("Biometric Device", device_name)
		adapter = self.get_adapter(device.device_type, device.as_dict())
		
		try:
			if adapter.test_connection():
				return f"Connection successful for {device.device_name}"
			else:
				return f"Connection failed for {device.device_name}"
		except Exception as e:
			return f"Connection error: {str(e)}"
	
	def sync_device(self, device_name: str):
		"""Sync a single biometric device"""
		device = frappe.get_doc("Biometric Device", device_name)
		
		if not device.enabled:
			frappe.throw(f"Device {device_name} is disabled")
		
		# Get last sync time
		last_sync = device.last_sync_time or datetime(1970, 1, 1)
		
		# Create adapter
		adapter = self.get_adapter(device.device_type, device.as_dict())
		
		try:
			# Fetch checkins
			checkins = adapter.fetch_checkins(last_sync)
			
			# Process checkins
			successful = 0
			failed = 0
			error_message = ""
			
			for checkin in checkins:
				try:
					self._create_employee_checkin(checkin, device.name)
					successful += 1
				except Exception as e:
					failed += 1
					if not error_message:
						error_message = str(e)
			
			# Update device sync status
			device.last_sync_time = frappe.utils.now_datetime()
			device.records_processed = len(checkins)
			device.successful_records = successful
			device.failed_records = failed
			if error_message:
				device.error_message = error_message[:140]  # Truncate if too long
			device.save(ignore_permissions=True)
			
			# Create sync log
			self._create_sync_log(device.name, len(checkins), successful, failed, error_message)
			
		except Exception as e:
			# Log error and update device
			device.error_message = str(e)[:140]
			device.save(ignore_permissions=True)
			self._create_sync_log(device.name, 0, 0, 1, str(e))
			raise
	
	def _create_employee_checkin(self, checkin: CheckinRecord, device_name: str):
		"""Create Employee Checkin record from biometric data"""
		# Check if employee exists
		employee_id_field = frappe.db.get_value("Biometric Device", device_name, "employee_id_field")
		employee_filters = {}
		
		if employee_id_field == "user_id":
			employee_filters["user_id"] = checkin.employee_id
		elif employee_id_field == "custom":
			# Handle custom mapping - this would need additional configuration
			employee_filters["name"] = checkin.employee_id
		else:
			# Default to employee_id
			employee_filters["employee"] = checkin.employee_id
		
		employee = frappe.db.get_value("Employee", employee_filters, "name")
		
		if not employee:
			frappe.throw(f"Employee not found for ID: {checkin.employee_id}")
		
		# Check for duplicate checkin
		existing = frappe.db.exists("Employee Checkin", {
			"employee": employee,
			"time": checkin.timestamp,
			"log_type": checkin.log_type
		})
		
		if existing:
			return  # Skip duplicate
		
		# Create Employee Checkin
		checkin_doc = frappe.get_doc({
			"doctype": "Employee Checkin",
			"employee": employee,
			"time": checkin.timestamp,
			"log_type": checkin.log_type,
			"device_id": device_name
		})
		checkin_doc.insert(ignore_permissions=True)
	
	def _create_sync_log(self, device_name: str, records_processed: int, 
						successful: int, failed: int, error_message: str = ""):
		"""Create biometric sync log entry"""
		status = "Success"
		if failed > 0 and successful > 0:
			status = "Partial"
		elif failed > 0:
			status = "Failed"
		
		log_doc = frappe.get_doc({
			"doctype": "Biometric Sync Log",
			"device": device_name,
			"sync_time": frappe.utils.now_datetime(),
			"records_processed": records_processed,
			"successful": successful,
			"failed": failed,
			"error_message": error_message[:500] if error_message else "",
			"status": status
		})
		log_doc.insert(ignore_permissions=True)


@frappe.whitelist()
def sync_single_device(device_name: str):
	"""Background job function to sync a single device"""
	manager = BiometricSyncManager()
	manager.sync_device(device_name)


@frappe.whitelist()
def sync_all_enabled_devices():
	"""Background job function to sync all enabled devices"""
	enabled_devices = frappe.get_all("Biometric Device", filters={"enabled": 1}, pluck="name")
	manager = BiometricSyncManager()
	
	for device_name in enabled_devices:
		try:
			manager.sync_device(device_name)
		except Exception as e:
			frappe.log_error(f"Error syncing device {device_name}: {str(e)}", "Biometric Sync Error")
