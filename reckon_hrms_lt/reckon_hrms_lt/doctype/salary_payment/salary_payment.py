# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_first_day, get_last_day, getdate, nowdate, today

from reckon_hrms_lt.utils import (
	calc_net_salary,
	calculate_attendance_deduction,
	get_attendance_summary,
	get_settings,
	validate_accounting_settings,
)

MONEY_FIELDS = ("gross_salary", "attendance_deduction", "total_allowance", "total_bonus", "total_other_deduction", "net_salary")
CHILD_TABLES = ("allowances", "bonuses", "deductions")
PAYMENT_FIELDS = ("status", "payment_date", "journal_entry", "bank_entry", "amended_reason", "mode_of_payment", "reference_no")


class SalaryPayment(Document):
	def before_validate(self):
		self.normalize_salary_month()

	def validate(self):
		self.validate_employee()
		self.validate_salary_month()
		self.validate_duplicate()
		self.validate_amounts()
		self.validate_locked()
		self.update_attendance_summary()
		self.calculate_all()

	def on_trash(self):
		if self.status != "Draft" and not self.flags.ignore_status_check:
			frappe.throw(_("Only Draft salary records can be deleted. Cancel the record instead."))

	def normalize_salary_month(self):
		if self.salary_month:
			self.salary_month = get_first_day(self.salary_month)
			self.salary_month_label = frappe.utils.formatdate(self.salary_month, "MMMM yyyy")

	def validate_employee(self):
		if not frappe.db.get_value("Employee", self.employee, "name"):
			frappe.throw(_("Employee {0} does not exist").format(self.employee))
		status = frappe.db.get_value("Employee", self.employee, "status")
		if status not in ("Active", "Left", "Suspended"):
			frappe.throw(_("Cannot process salary for employee with status {0}").format(status))

	def validate_salary_month(self):
		if getdate(self.salary_month) > getdate(nowdate()):
			frappe.throw(_("Salary month cannot be in the future"))

	def validate_duplicate(self):
		# prevent duplicate salary records for the same employee and month
		filters = {
			"employee": self.employee,
			"salary_month": self.salary_month,
			"status": ("!=", "Cancelled"),
			"name": ("!=", self.name or ""),
		}
		existing = frappe.db.get_value("Salary Payment", filters, ["name", "status"], as_dict=True)
		if existing:
			frappe.throw(
				_("Salary for {0} ({1}) already exists: {2}").format(
					self.employee_name or self.employee, self.salary_month_label, existing.name
				),
				title=_("Duplicate Salary"),
			)

	def validate_amounts(self):
		if flt(self.gross_salary) < 0:
			frappe.throw(_("Gross Salary cannot be negative"))

		for table_name in CHILD_TABLES:
			for row in self.get(table_name) or []:
				if flt(row.amount) < 0:
					frappe.throw(_("Negative amounts are not allowed in {0}").format(self.meta.get_label(table_name)))

	def validate_locked(self):
		"""Block modification of financial data after submission / payment."""
		if self.flags.ignore_locked_validation or self.is_new():
			return

		db_doc = self.get_doc_before_save()
		if not db_doc:
			return

		if db_doc.status == "Draft":
			return

		if db_doc.status in ("Submitted", "Paid", "Cancelled"):
			if flt(db_doc.gross_salary) != flt(self.gross_salary):
				frappe.throw(_("Gross Salary cannot be changed after submission (status: {0})").format(db_doc.status))

			for table_name in CHILD_TABLES:
				old_rows = [(r.name, flt(r.amount), r.allowance_type if hasattr(r, "allowance_type") else None) for r in db_doc.get(table_name) or []]
				new_rows = [(r.name, flt(r.amount), r.allowance_type if hasattr(r, "allowance_type") else None) for r in self.get(table_name) or []]
				if old_rows != new_rows:
					frappe.throw(
						_("{0} cannot be changed after submission (status: {1})").format(self.meta.get_label(table_name), db_doc.status)
					)

		if db_doc.status in ("Paid", "Cancelled"):
			changed = [
				df
				for df in self.meta.fields
				if df.fieldtype not in ("Section Break", "Column Break", "HTML")
				and df.fieldname not in PAYMENT_FIELDS
				and db_doc.get(df.fieldname) != self.get(df.fieldname)
			]
			if changed:
				frappe.throw(
					_("A {0} salary record is locked and cannot be modified.").format(db_doc.status)
				)

	def update_attendance_summary(self):
		"""Read attendance from standard Frappe HR Attendance records."""
		if not self.employee or not self.salary_month:
			return
		summary = get_attendance_summary(self.employee, self.salary_month)
		self.present_days = flt(summary["present"], 2)
		self.absent_days = flt(summary["absent"], 2)
		self.half_day_count = flt(summary["half_day"], 2)
		self.late_count = int(summary["late"])
		self.leave_days = flt(summary["on_leave"], 2)

	def calculate_all(self):
		"""Authoritative server-side salary calculation."""
		settings = get_settings()

		self.total_allowance = flt(sum(flt(r.amount) for r in self.allowances or []), 2)
		self.total_bonus = flt(sum(flt(r.amount) for r in self.bonuses or []), 2)
		self.total_other_deduction = flt(sum(flt(r.amount) for r in self.deductions or []), 2)

		self.attendance_deduction = flt(
			calculate_attendance_deduction(
				gross_salary=flt(self.gross_salary),
				working_days=int(settings.working_days or 30),
				absent_days=flt(self.absent_days),
				half_day_count=flt(self.half_day_count),
				late_count=int(self.late_count or 0),
				absent_deduction_per_day=flt(settings.absent_deduction_per_day, 3),
				late_count_for_deduction=int(settings.late_count_for_deduction or 3),
				half_day_deduction=flt(settings.half_day_deduction, 3),
			),
			2,
		)

		self.net_salary = flt(
			calc_net_salary(
				gross_salary=flt(self.gross_salary),
				total_allowance=flt(self.total_allowance),
				total_bonus=flt(self.total_bonus),
				attendance_deduction=flt(self.attendance_deduction),
				total_other_deduction=flt(self.total_other_deduction),
			),
			2,
		)

		if self.net_salary < 0:
			frappe.throw(
				_("Net Salary cannot be negative ({0}). Reduce deductions.").format(self.net_salary)
			)

	# ------------------------------------------------------------------ #
	# User actions
	# ------------------------------------------------------------------ #

	@frappe.whitelist()
	def calculate(self):
		"""Recalculate salary for the current values. Used by the [Calculate] button."""
		if self.status in ("Paid", "Cancelled"):
			frappe.throw(_("A {0} salary record cannot be recalculated.").format(self.status))

		self.update_attendance_summary()
		self.calculate_all()

		return {
			"present_days": self.present_days,
			"absent_days": self.absent_days,
			"half_day_count": self.half_day_count,
			"late_count": self.late_count,
			"leave_days": self.leave_days,
			"attendance_deduction": self.attendance_deduction,
			"total_allowance": self.total_allowance,
			"total_bonus": self.total_bonus,
			"total_other_deduction": self.total_other_deduction,
			"net_salary": self.net_salary,
		}

	@frappe.whitelist()
	def submit_salary(self):
		"""Move Draft -> Submitted. Financial values are locked from now on."""
		if self.status != "Draft":
			frappe.throw(_("Only Draft salary records can be submitted."))

		self.calculate_all()
		if flt(self.gross_salary) <= 0:
			frappe.throw(_("Enter a Gross Salary before submitting."))
		if flt(self.net_salary) < 0:
			frappe.throw(_("Net Salary cannot be negative."))

		self.db_set("status", "Submitted", update_modified=False)
		frappe.msgprint(_("Salary submitted. You can now pay the salary."))

	@frappe.whitelist()
	def pay_salary(self, mode_of_payment=None):
		"""Pay the salary: create native ERPNext accounting entries in the background.

		Accounting flow:
		  Journal Entry (accrual):   Salary Expense (Dr)  / Salary Payable (Cr)
		  Journal Entry (payment):   Salary Payable (Dr)  / Bank or Cash (Cr)
		"""
		if self.status == "Paid":
			frappe.throw(_("This salary has already been paid."))

		if self.status == "Cancelled":
			frappe.throw(_("This salary record is cancelled."))

		if self.status == "Draft":
			frappe.throw(_("Submit the salary record before paying."))

		if flt(self.net_salary) <= 0:
			frappe.throw(_("Net Salary must be greater than zero to pay."))

		mode_of_payment = mode_of_payment or self.mode_of_payment or "Bank"
		if mode_of_payment not in ("Bank", "Cash"):
			frappe.throw(_("Payment method must be Bank or Cash."))

		settings = get_settings()
		target_account = validate_accounting_settings(settings, mode_of_payment, self.company)

		# Idempotency: never create duplicate accounting transactions on retry
		accrual_entry = self.get_existing_entry(self.journal_entry)
		payment_entry = self.get_existing_entry(self.bank_entry)

		if payment_entry:
			self._mark_paid(mode_of_payment, accrual_entry, payment_entry)
			return

		frappe.db.savepoint("pay_salary")
		try:
			amount = flt(self.net_salary, 2)
			posting_date = today()

			if not accrual_entry:
				accrual_entry = self._create_accrual_entry(settings, amount, posting_date)

			payment_entry = self._create_payment_entry(settings, target_account, amount, posting_date, mode_of_payment)

			self._mark_paid(mode_of_payment, accrual_entry.name, payment_entry.name, posting_date)
			frappe.db.commit()

			frappe.msgprint(
				_("Salary paid. Accrual: {0}, Payment: {1}").format(accrual_entry.name, payment_entry.name),
				title=_("Paid"),
				indicator="green",
			)
		except Exception:
			frappe.db.rollback(save_point="pay_salary")
			frappe.log_error(
				frappe.get_traceback(),
				f"Salary payment failed for {self.name}",
			)
			frappe.throw(
				_("Salary payment failed. The salary remains UNPAID and no accounting entries were posted. "
				  "Please check the accounting configuration in Reckon HRMS Settings and retry.<br><br>Error: {0}").format(
					frappe.utils.cstr(frappe.get_traceback()).splitlines()[-1]
				)
			)

	@frappe.whitelist()
	def cancel_salary(self, reason=None):
		"""Controlled cancellation. Reverses accounting via ERPNext standard cancellation.

		Accounting documents are cancelled (not deleted) and stay linked for audit.
		"""
		if self.status == "Cancelled":
			frappe.throw(_("This salary record is already cancelled."))

		if self.status not in ("Submitted", "Paid"):
			frappe.throw(_("Only Submitted or Paid salary records can be cancelled."))

		if not reason:
			frappe.throw(_("Please provide a cancellation reason."))

		frappe.db.savepoint("cancel_salary")
		try:
			for entry_name in (self.bank_entry, self.journal_entry):
				entry = self.get_existing_entry(entry_name)
				if entry and entry.docstatus == 1:
					entry.flags.ignore_permissions = True
					entry.cancel()

			self.flags.ignore_locked_validation = True
			self.db_set("status", "Cancelled", update_modified=False)
			self.db_set("amended_reason", reason, update_modified=False)
			frappe.db.commit()

			frappe.msgprint(_("Salary cancelled. Accounting entries were reversed via standard cancellation."))
		except Exception:
			frappe.db.rollback(save_point="cancel_salary")
			frappe.log_error(frappe.get_traceback(), f"Salary cancellation failed for {self.name}")
			raise

	def get_existing_entry(self, entry_name):
		if entry_name and frappe.db.exists("Journal Entry", entry_name):
			return frappe.get_doc("Journal Entry", entry_name)
		return None

	def _create_accrual_entry(self, settings, amount, posting_date):
		je = frappe.get_doc(
			{
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"company": settings.company,
				"posting_date": posting_date,
				"remark": _("Salary accrual for {0} - {1}").format(self.employee_name or self.employee, self.salary_month_label),
				"accounts": [
					{
						"account": settings.salary_expense_account,
						"debit_in_account_currency": amount,
						"credit_in_account_currency": 0,
						"cost_center": settings.cost_center,
						"user_remark": _("{0} - {1}").format(self.employee_name or self.employee, self.salary_month_label),
					},
					{
						"account": settings.salary_payable_account,
						"debit_in_account_currency": 0,
						"credit_in_account_currency": amount,
						"cost_center": settings.cost_center,
						"user_remark": _("{0} - {1}").format(self.employee_name or self.employee, self.salary_month_label),
					},
				],
			}
		)
		je.flags.ignore_permissions = True
		je.insert()
		je.submit()
		return je

	def _create_payment_entry(self, settings, target_account, amount, posting_date, mode_of_payment):
		je = frappe.get_doc(
			{
				"doctype": "Journal Entry",
				"voucher_type": "Bank Entry" if mode_of_payment == "Bank" else "Cash Entry",
				"company": settings.company,
				"posting_date": posting_date,
				"cheque_no": self.reference_no,
				"cheque_date": posting_date if self.reference_no else None,
				"remark": _("Salary payment for {0} - {1}").format(self.employee_name or self.employee, self.salary_month_label),
				"accounts": [
					{
						"account": settings.salary_payable_account,
						"debit_in_account_currency": amount,
						"credit_in_account_currency": 0,
						"cost_center": settings.cost_center,
						"user_remark": _("{0} - {1}").format(self.employee_name or self.employee, self.salary_month_label),
					},
					{
						"account": target_account,
						"debit_in_account_currency": 0,
						"credit_in_account_currency": amount,
						"cost_center": settings.cost_center,
						"user_remark": _("{0} - {1}").format(self.employee_name or self.employee, self.salary_month_label),
					},
				],
			}
		)
		je.flags.ignore_permissions = True
		je.insert()
		je.submit()
		return je

	def _mark_paid(self, mode_of_payment, accrual_name, payment_name, posting_date=None):
		self.flags.ignore_locked_validation = True
		self.db_set("status", "Paid", update_modified=False)
		self.db_set("mode_of_payment", mode_of_payment, update_modified=False)
		self.db_set("journal_entry", accrual_name, update_modified=False)
		self.db_set("bank_entry", payment_name, update_modified=False)
		if posting_date and not self.payment_date:
			self.db_set("payment_date", posting_date, update_modified=False)


@frappe.whitelist()
def get_default_gross_salary(employee):
	"""Return the default gross salary configured on the Employee (custom field)."""
	return flt(frappe.db.get_value("Employee", employee, "gross_salary") or 0, 2)


@frappe.whitelist()
def pay_salary_payments(names):
	"""Pay multiple Salary Payment records (used by Bulk Salary). Runs each independently."""
	import json

	if isinstance(names, str):
		names = json.loads(names)

	results = {"paid": [], "failed": []}
	for name in names:
		doc = frappe.get_doc("Salary Payment", name)
		try:
			if doc.status != "Paid":
				doc.pay_salary()
			results["paid"].append(name)
		except Exception:
			results["failed"].append({"name": name, "error": frappe.get_traceback()})
			frappe.log_error(frappe.get_traceback(), f"Bulk salary payment failed for {name}")

	return results
