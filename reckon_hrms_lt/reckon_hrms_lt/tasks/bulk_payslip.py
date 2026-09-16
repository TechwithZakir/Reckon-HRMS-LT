# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

"""Background tasks for Bulk Salary Processing."""

import frappe
from frappe import _
from frappe.utils import now, today
from frappe.utils.pdf import get_pdf


def pay_bulk_salaries(bulk_name):
	"""Background job: Process all salary payments in a bulk document.

	Updates status on each Salary Payment and the bulk document.
	"""
	bulk = frappe.get_doc("Bulk Salary Payment", bulk_name)
	status_updated = False

	for row in bulk.bulk_salary_employees:
		if row.payment_status != "Draft":
			continue

		try:
			sp = frappe.get_doc("Salary Payment", row.salary_payment)
			sp.pay_salary()
			row.payment_status = "Paid"
			status_updated = True
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), f"Bulk salary payment failed for {row.salary_payment}")
			row.payment_status = "Failed"
			row.amended_reason = str(e)[:140]

	if status_updated:
		bulk.update_status()
		bulk.save(ignore_permissions=True)
		frappe.db.commit()

	# If any were processed successfully, show a message
	if bulk.status == "Paid":
		frappe.publish_realtime(
			"bulk_salary_paid",
			{
				"bulk_name": bulk.name,
				"message": _("All salaries have been paid successfully")
			},
		)


def generate_bulk_payslips_pdf(bulk_name):
	"""Background job: Generate a combined PDF of all payslips in a bulk document.

	Saves the PDF as a File attachment to the bulk document.
	"""
	bulk = frappe.get_doc("Bulk Salary Payment", bulk_name)

	if not bulk.bulk_salary_employees:
		frappe.throw(_("No employees found in this bulk salary record"))

	# Build HTML for all payslips
	html = []
	html.append(f"<h1>{bulk.company} Salary Payslips - {bulk.salary_month.strftime('%B %Y')}</h1>")

	for row in bulk.bulk_salary_employees:
		if not row.salary_payment:
			continue

		sp = frappe.get_doc("Salary Payment", row.salary_payment)
		try:
			payslip_html = frappe.get_print(
				"Salary Payment",
				sp.name,
				"Reckon Payslip",
			)
			html.append(f"<div class='page-break'>{payslip_html}</div>")
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), f"Payslip generation failed for {row.employee}")

	if not html:
		frappe.throw(_("No payslips could be generated"))

	# Generate PDF
	try:
		pdf_content = get_pdf("\n".join(html), options={"page-size": "A4"})

		# Save as file
		file_name = f"Bulk-Payslips-{bulk.name}.pdf"
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": file_name,
			"is_private": 1,
			"content": pdf_content,
		}).insert(ignore_permissions=True)

		# Link to bulk document
		bulk.db_set("_payslip_pdf", file_doc.file_url)
		bulk.save(ignore_permissions=True)

		# Notify user
		frappe.publish_realtime(
			"bulk_payslip_ready",
			{
				"bulk_name": bulk.name,
				"file_url": file_doc.file_url,
				"message": _("Payslips PDF is ready")
			},
		)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Bulk payslip PDF generation failed")
		raise