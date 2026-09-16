// Copyright (c) 2026, Reckon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bulk Salary Payment", {
	refresh(frm) {
		frm.trigger("add_actions");
	},

	add_actions(frm) {
		if (frm.is_new()) return;

		if (frm.doc.status === "Draft") {
			frm.add_custom_button(__("Generate Salaries"), () => {
				frappe.confirm(
					__("This will fetch all matching employees and create draft salary records. Continue?"),
					() => {
						frm.call({
							doc: frm.doc,
							method: "generate_salaries",
							freeze: true,
							freeze_message: __("Generating salary records..."),
						}).then(() => frm.reload_doc());
					}
				);
			});
			frm.page.set_primary_action(__("Save"), () => frm.save());
		}

		if (["Draft", "Generated"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Calculate All"), () => {
				frm.call({
					doc: frm.doc,
					method: "calculate_all",
					freeze: true,
				}).then(() => frm.reload_doc());
			}, __("Actions"));
		}

		if (["Generated", "Draft"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Submit All"), () => {
				frappe.confirm(
					__("Submit all salary records? Financial values will be locked."),
					() => {
						frm.call({
							doc: frm.doc,
							method: "submit_all",
							freeze: true,
						}).then(() => frm.reload_doc());
					}
				);
			}, __("Actions"));
		}

		if (["Generated", "Submitted"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Pay All"), () => {
				frappe.confirm(
					__("Process payment for all generated salaries via ERPNext Accounting?"),
					() => {
						frm.call({
							doc: frm.doc,
							method: "pay_all",
							freeze: true,
							freeze_message: __("Initiating bulk payment..."),
						}).then(() => frm.reload_doc());
					}
				);
			});
			frm.page.set_primary_action(__("Pay All"), () => frm.trigger("add_actions"));
		}

		if (frm.doc.bulk_salary_employees && frm.doc.bulk_salary_employees.length > 0) {
			frm.add_custom_button(__("Print All Payslips"), () => {
				frm.call({
					doc: frm.doc,
					method: "print_all_payslips",
					freeze: true,
					freeze_message: __("Generating payslips PDF..."),
				}).then(() => {
					frappe.msgprint(
						__("Payslip PDF generation has been started. You will be notified when it is ready.")
					);
				});
			});
		}
	},
});

frappe.ui.form.on("Bulk Salary Employee", {
	gross_salary(frm, cdt, cdn) { recalc_row(frm, cdt, cdn); },
	allowance_total(frm, cdt, cdn) { recalc_row(frm, cdt, cdn); },
	bonus_total(frm, cdt, cdn) { recalc_row(frm, cdt, cdn); },
	other_deduction_total(frm, cdt, cdn) { recalc_row(frm, cdt, cdn); },
});

function recalc_row(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	row.net_salary = flt(row.gross_salary) + flt(row.allowance_total) + flt(row.bonus_total) - flt(row.attendance_deduction) - flt(row.other_deduction_total);
	frappe.model.set_value(cdt, cdn, "net_salary", flt(row.net_salary, 2));
	frm.refresh_field("bulk_salary_employees");
}

function flt(v) {
	return parseFloat(v || 0) || 0;
}