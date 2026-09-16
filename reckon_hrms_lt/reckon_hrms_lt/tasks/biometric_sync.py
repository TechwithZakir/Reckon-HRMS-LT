# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

import frappe


def sync_biometric_devices():
    """Scheduled task to sync all enabled biometric devices"""
    from reckon_hrms_lt.biometric.manager import sync_all_enabled_devices
    
    if frappe.db.exists("DocType", "Biometric Device"):
        sync_all_enabled_devices()