# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

"""Unit tests for pure calculation functions in utils.py."""

import unittest

from reckon_hrms_lt.utils import calc_net_salary, calculate_attendance_deduction


class TestSalaryCalculations(unittest.TestCase):
	"""Test pure salary calculation logic (no DB required)."""

	def test_net_salary_basic(self):
		self.assertEqual(calc_net_salary(30000), 30000)

	def test_net_salary_with_allowances(self):
		result = calc_net_salary(30000, total_allowance=2000, total_bonus=1000)
		self.assertEqual(result, 33000)

	def test_net_salary_with_deductions(self):
		result = calc_net_salary(30000, attendance_deduction=3000, total_other_deduction=500)
		self.assertEqual(result, 26500)

	def test_net_salary_full(self):
		result = calc_net_salary(30000, 2000, 1000, 3000, 500)
		self.assertEqual(result, 29500)

	def test_net_salary_negative(self):
		result = calc_net_salary(1000, 0, 0, 3000, 0)
		self.assertEqual(result, -2000)

	def test_attendance_deduction_absent(self):
		# 30000 gross / 30 days = 1000 per day, 2 absent
		result = calculate_attendance_deduction(30000, 30, absent_days=2)
		self.assertEqual(result, 2000)

	def test_attendance_deduction_late(self):
		# 30000 / 30 = 1000, 3 late = 1 day deduction
		result = calculate_attendance_deduction(
			30000, 30, late_count=3, late_count_for_deduction=3
		)
		self.assertEqual(result, 1000)

	def test_attendance_deduction_half_day(self):
		# 30000 / 30 = 1000, 1 half day = 0.5 * 1000
		result = calculate_attendance_deduction(
			30000, 30, half_day_count=1, half_day_deduction=0.5
		)
		self.assertAlmostEqual(result, 500)

	def test_attendance_deduction_combined(self):
		result = calculate_attendance_deduction(
			30000, 30,
			absent_days=2, half_day_count=1, late_count=3,
			absent_deduction_per_day=1,
			late_count_for_deduction=3,
			half_day_deduction=0.5,
		)
		# 2 absent = 2000, 1 half day = 500, 3 late = 1000
		self.assertEqual(result, 3500)
