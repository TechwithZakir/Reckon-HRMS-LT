# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class CheckinRecord:
	"""Represents a single check-in record from a biometric device"""
	employee_id: str
	timestamp: datetime
	device_id: str
	log_type: str = "IN"  # IN or OUT


class BiometricAdapter(ABC):
	"""Abstract base class for biometric device adapters"""
	
	@abstractmethod
	def test_connection(self) -> bool:
		"""Test connection to the device"""
		pass
	
	@abstractmethod
	def fetch_checkins(self, since: datetime) -> List[CheckinRecord]:
		"""Fetch check-in records from the device since the given timestamp"""
		pass
	
	@abstractmethod
	def disconnect(self):
		"""Disconnect from the device"""
		pass
