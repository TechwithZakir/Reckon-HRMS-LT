// Copyright (c) 2026, Reckon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Biometric Device", {
	refresh(frm) {
		frm.add_custom_button(__("Test Connection"), function () {
			frm.call({
				doc: frm.doc,
				method: "test_connection",
				freeze: true,
				freeze_message: __("Testing connection..."),
			});
		});

		frm.add_custom_button(__("Sync Now"), function () {
			frm.call({
				doc: frm.doc,
				method: "sync_now",
				freeze: true,
				freeze_message: __("Starting sync..."),
			});
		});

		if (!frm.is_new()) {
			frm.fields_dict.sync_logs &&
				$(frm.fields_dict.sync_logs.wrapper).html(
					`<a href="/app/biometric-sync-log?device=${encodeURIComponent(frm.doc.name)}">${__("View all sync logs")}</a>`
				);
		}
	},
});
