// Copyright (c) 2026, Reckon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Payment", {
	setup(frm) {
		frm.set_query("employee", function () {
			return { filters: { status: ["in", ["Active", "Left", "Suspended"]] } };
		});
	},

	refresh(frm) {
		frm.trigger("set_readonly_state");
		frm.trigger("add_actions");

		if (frm.doc.__islocal && frappe.user.has_role(["HR Manager", "HR User", "System Manager"])) {
			frm.set_value("salary_month", frappe.datetime.month_start());
		}
	},

	employee(frm) {
		if (!frm.doc.employee) return;
		// pull default gross salary from the employee record
		frappe.call({
			method: "reckon_hrms_lt.reckon_hrms.doctype.salary_payment.salary_payment.get_default_gross_salary",
			args: { employee: frm.doc.employee },
			callback(r) {
				if (r.message && (!frm.doc.gross_salary || frm.doc.gross_salary == 0)) {
					frm.set_value("gross_salary", r.message);
				}
			},
		});
		frm.trigger("calculate_salary");
	},

	salary_month(frm) {
		frm.trigger("calculate_salary");
	},

	gross_salary(frm) {
		frm.trigger("calculate_salary");
	},

	calculate_salary(frm) {
		if (!frm.doc.employee || !frm.doc.salary_month || frm.doc.status === "Paid") return;
		frm.call({
			doc: frm.doc,
			method: "calculate",
			args: {},
			callback(r) {
				if (r.message) {
					Object.keys(r.message).forEach((key) => frm.set_value(key, r.message[key]));
					frm.refresh_fields([
						"present_days", "absent_days", "half_day_count", "late_count", "leave_days",
						"attendance_deduction", "total_allowance", "total_bonus",
						"total_other_deduction", "net_salary",
					]);
				}
			},
		});
	},

	set_readonly_state(frm) {
		const locked = ["Paid", "Cancelled"].includes(frm.doc.status);
		const money_fields = ["gross_salary", "allowances", "bonuses", "deductions"];

		if (locked) {
			frm.disable_save();
			money_fields.forEach((f) => frm.set_df_property(f, "read_only", 1));
		} else if (frm.doc.status === "Submitted") {
			money_fields.forEach((f) => frm.set_df_property(f, "read_only", 1));
		}

		if (frm.doc.status === "Paid" && frm.doc.bank_entry) {
			frm.dashboard.clear_headline();
			frm.dashboard.set_headline_alert(
				`<div class="text-muted">${__("This salary is PAID.")}
					<a href="/app/journal-entry/${frm.doc.journal_entry}">${__("View Accrual Entry")}</a> |
					<a href="/app/journal-entry/${frm.doc.bank_entry}">${__("View Payment Entry")}</a>
				</div>`
			);
		}
	},

	add_actions(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Calculate"), function () {
			frm.trigger("calculate_salary");
			frm.dirty() || frm.save();
		});

		if (frm.doc.status === "Draft") {
			frm.add_custom_button(
				__("Submit"),
				function () {
					frappe.confirm(
						__("Submit this salary? Financial values will be locked."),
						() => {
							frm.save().then(() => {
								frm.call({ doc: frm.doc, method: "submit_salary" }).then(() => frm.reload_doc());
							});
						}
					);
				},
				__("Actions")
			);
			frm.page.set_primary_action(__("Save"), () => frm.save());
		}

		if (frm.doc.status === "Submitted") {
			frm.add_custom_button(__("Pay Salary"), function () {
				frm.events.do_pay(frm);
			});
			frm.page.set_primary_action(__("Pay Salary"), () => frm.events.do_pay(frm));
			frm.add_custom_button(
				__("Cancel Salary"),
				function () {
					frm.events.do_cancel(frm);
				},
				__("Actions")
			);
		}

		if (frm.doc.status === "Paid") {
			frm.page.set_primary_action(__("Print Payslip"), () => frm.print_preview.printit(frm.doctype, null, frm.docname));
			frm.add_custom_button(__("Cancel Salary"), function () {
				frm.events.do_cancel(frm);
			});
		}

		if (!["Paid", "Cancelled"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Print Payslip"), function () {
				frm.print_preview.printit(frm.doctype, "Reckon Payslip", frm.docname);
			});
		}
	},

	do_pay(frm) {
		const d = new frappe.ui.Dialog({
			title: __("Pay Salary"),
			fields: [
				{
					fieldname: "mode_of_payment",
					label: __("Payment Method"),
					fieldtype: "Select",
					options: ["Bank", "Cash"],
					default: frm.doc.mode_of_payment || "Bank",
					reqd: 1,
				},
				{
					fieldname: "reference_no",
					label: __("Reference No (cheque / transaction)"),
					fieldtype: "Data",
					default: frm.doc.reference_no,
				},
				{ fieldtype: "HTML", fieldname: "summary" },
			],
			primary_action_label: __("Pay Now"),
			primary_action(values) {
				d.hide();
				frm.set_value("mode_of_payment", values.mode_of_payment);
				if (values.reference_no) frm.set_value("reference_no", values.reference_no);
				frm.save().then(() => {
					frm.call({
						doc: frm.doc,
						method: "pay_salary",
						args: { mode_of_payment: values.mode_of_payment },
						freeze: true,
						freeze_message: __("Processing payment..."),
					}).then(() => frm.reload_doc());
				});
			},
		});
		d.fields_dict.summary.$wrapper.html(
			`<div class="small text-muted mt-2">${__("Employee")}: <b>${frm.doc.employee_name || frm.doc.employee}</b><br>
			${__("Month")}: <b>${frm.doc.salary_month_label || ""}</b><br>
			${__("Net Salary")}: <b>${format_currency(frm.doc.net_salary)}</b></div>`
		);
		d.show();
	},

	do_cancel(frm) {
		const d = new frappe.ui.Dialog({
			title: __("Cancel Salary"),
			fields: [
				{
					fieldtype: "Small Text",
					fieldname: "reason",
					label: __("Cancellation Reason"),
					reqd: 1,
				},
				{
					fieldtype: "HTML",
					fieldname: "note",
					options: `<p class="small text-muted">${__(
						"Accounting entries will be reversed using standard ERPNext cancellation. Records are kept for audit."
					)}</p>`,
				},
			],
			primary_action_label: __("Cancel Salary"),
			primary_action(values) {
				d.hide();
				frm.call({
					doc: frm.doc,
					method: "cancel_salary",
					args: { reason: values.reason },
					freeze: true,
				}).then(() => frm.reload_doc());
			},
		});
		d.show();
	},
});
