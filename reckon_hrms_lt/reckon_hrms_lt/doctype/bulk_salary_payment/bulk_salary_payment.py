# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, flt, get_first_day

from reckon_hrms_lt.utils import (
	get_employees_for_bulk,
	get_settings,
	calculate_attendance_deduction,
	calc_net_salary,
)


class BulkSalaryPayment(Document):
	def before_validate(self):
		if self.salary_month and not self.is_new_or_status_changed():
			self.salary_month = get_first_day(self.salary_month)

	def validate(self):
		self.validate_salary_month()
		self.validate_duplicate()
		self.sync_salary_payments()
		self.calculate_all_rows()

	def validate_salary_month(self):
		if self.salary_month and frappe.utils.getdate(self.salary_month) > frappe.utils.getdate(today()):
			frappe.throw(_("Salary month cannot be in the future"))

	def validate_duplicate(self):
		if self.is_new() or self.has_value_changed("salary_month") or self.has_value_changed("company"):
			filters = {
				"company": self.company,
				"salary_month": self.salary_month,
				"name": ("!=", self.name or ""),
			}
			if self.status and self.status != "Cancelled":
				filters["status"] = ("!=", "Cancelled")
			if frappe.db.get_value("Bulk Salary Payment", filters):
				frappe.throw(_("A bulk salary record already exists for this company and month"))

	def sync_salary_payments(self):
		"""Update linked Draft Salary Payments when row values change."""
		for row in self.bulk_salary_employees or []:
			if not row.salary_payment:
				continue
			try:
				sp = frappe.get_doc("Salary Payment", row.salary_payment)
				if sp.status != "Draft":
					continue

				sp.flags.ignore_locked_validation = True
				changed = False
				if flt(sp.gross_salary) != flt(row.gross_salary):
					sp.gross_salary = row.gross_salary
					changed = True
				sp.calculate_all()

				if changed:
					sp.save(ignore_permissions=True)
			except Exception:
				pass  # Best effort sync; errors are logged silently

	def calculate_all_rows(self):
		"""Recalculate row totals from linked Salary Payments or settings."""
		settings = frappe.get_cached_doc("Reckon HRMS Settings")

		for row in self.bulk_salary_employees or []:
			if row.salary_payment:
				try:
					sp = frappe.get_cached_doc("Salary Payment", row.salary_payment)
					row.attendance_deduction = flt(sp.attendance_deduction, 2)
					row.allowance_total = flt(sp.total_allowance, 2)
					row.bonus_total = flt(sp.total_bonus, 2)
					row.other_deduction_total = flt(sp.total_other_deduction, 2)
				except Exception:
					row.attendance_deduction = 0
					row.allowance_total = 0
					row.bonus_total = 0
					row.other_deduction_total = 0

			row.net_salary = calc_net_salary(
				row.gross_salary,
				row.allowance_total,
				row.bonus_total,
				row.attendance_deduction,
				row.other_deduction_total,
			)

	# ------------------------------------------------------------------ #
	# Whitelisted user actions
	# ------------------------------------------------------------------ #

	@frappe.whitelist()
	def generate_salaries(self):
		"""Generate salary rows for employees matching filters and create Draft Salary Payments."""
		if self.status not in ("Draft",):
			frappe.throw(_("Can only generate salaries from a Draft bulk salary record"))

		self.bulk_salary_employees = []
		month_start = get_first_day(self.salary_month)

		employees = get_employees_for_bulk(
			self.company,
			self.department,
			self.employee_type,
			self.grade
		)

		if not employees:
			frappe.throw(_("No employees found with the given filters"))

		for emp in employees:
			# Check for existing Salary Payment
			existing = frappe.db.get_all(
				"Salary Payment",
				filters={
					"employee": emp.name,
					"salary_month": month_start,
					"status": ["!=", "Cancelled"],
				},
				fields=["name"],
				limit=1,
			)

			salary_payment_name = existing[0].name if existing else None

			if not salary_payment_name:
				sp = frappe.get_doc({
					"doctype": "Salary Payment",
					"employee": emp.name,
					"company": self.company,
					"salary_month": month_start,
					"gross_salary": emp.gross_salary or 0,
					"status": "Draft",
				})
				sp.flags.ignore_permissions = True
				sp.insert()
				salary_payment_name = sp.name

			row = self.append("bulk_salary_employees", {
				"employee": emp.name,
				"employee_name": emp.employee_name,
				"department": emp.department,
				"gross_salary": flt(emp.gross_salary or 0),
				"salary_payment": salary_payment_name,
				"payment_status": "Draft",
			})

		# Recalculate row values from the newly created Salary Payments
		self.calculate_all_rows()
		self.db_set("status", "Generated", update_modified=True)
		frappe.msgprint(
			_("Generated {0} salary rows.").format(len(self.bulk_salary_employees)),
			indicator="green",
		)

	@frappe.whitelist()
	def calculate_all(self):
		"""Recalculate and refresh attendance + deductions from all linked Salary Payments."""
		for row in self.bulk_salary_employees or []:
			if row.salary_payment:
				try:
					sp = frappe.get_doc("Salary Payment", row.salary_payment)
					sp.update_attendance_summary()
					sp.calculate_all()
					sp.save(ignore_permissions=True)
				except Exception:
					pass

		self.calculate_all_rows()

	@frappe.whitelist()
	def submit_all(self):
		"""Submit all Draft Salary Payments linked to this bulk record."""
		if self.status not in ("Generated", "Draft"):
			frappe.throw(_("Can only submit salary payments that have been generated"))

		saved = 0
		for row in self.bulk_salary_employees or []:
			if row.payment_status == "Draft" and row.salary_payment:
				try:
					sp = frappe.get_doc("Salary Payment", row.salary_payment)
					sp.submit_salary()
					row.payment_status = "Submitted"
					saved += 1
				except Exception as e:
					frappe.log_error(
						frappe.get_traceback(),
						f"Bulk submit failed for {row.employee}: {row.salary_payment}",
					)
					row.payment_status = "Failed"

		self.status = "Submitted"
		frappe.msgprint(_("{0} salary records submitted.").format(saved), indicator="green")

	@frappe.whitelist()
	def pay_all(self):
		"""Pay all submitted Salary Payments in the background."""
		names = [
			row.salary_payment
			for row in self.bulk_salary_employees or []
			if row.salary_payment and row.payment_status == "Submitted"
		]
		if not names:
			frappe.throw(_("No submitted salary payments to pay."))

		frappe.msgprint(_("Payment for {0} salary records started in background.").format(len(names)))
		frappe.enqueue(
			"reckon_hrms_lt.doctype.salary_payment.salary_payment.pay_salary_payments",
			names=names,
			queue="long",
			timeout=3600,
		)

	@frappe.whitelist()
	def print_all_payslips(self):
		"""Generate a combined payslip PDF for all employees."""
		frappe.msgprint(_("Payslip PDF is being generated in background. The file will be attached to this record."))
		frappe.enqueue(
			"reckon_hrms_lt.tasks.bulk_payslip.generate_bulk_payslips_pdf",
			bulk_name=self.name,
			queue="long",
			timeout=3600,
		)
