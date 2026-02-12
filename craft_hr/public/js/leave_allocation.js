frappe.ui.form.on("Leave Allocation", {
    refresh: function(frm) {
        frappe.db.get_single_value("Craft HR Settings", "leave_allocation_based_on_leave_distribution_template").then((value) => {
            frm.toggle_display("custom_is_earned_leave", value);
            if (frm.doc.docstatus != 1 && frm.doc.custom_is_earned_leave && !value) {
                frm.set_value("custom_is_earned_leave", 0);
            }
        });

        // Add Close/Reopen buttons for HR Manager only
        if (frm.doc.docstatus === 1 && frappe.user.has_role('HR Manager')) {
            if (frm.doc.custom_status === "Ongoing") {
                frm.add_custom_button(__('Close Allocation'), function() {
                    if (frm.doc.from_date < frappe.datetime.get_today()) {
                        frappe.confirm(
                            __("Are you sure you want to close this allocation? This will update the allocation end date to today."),
                            function() {
                                frappe.call({
                                    method: "craft_hr.events.leave_allocation.close_allocation",
                                    args: {
                                        docname: frm.doc.name
                                    },
                                    callback: function(r) {
                                        if (!r.exc) {
                                            frm.reload_doc();
                                        }
                                    }
                                });
                            }
                        );
                    } else {
                        frappe.msgprint(__("This leave allocation period has not started yet."));
                    }
                }, __('Actions'));
            } else if (frm.doc.custom_status === "Closed") {
                frm.add_custom_button(__('Reopen Allocation'), function() {
                    frappe.confirm(
                        __("Are you sure you want to reopen this allocation?"),
                        function() {
                            frappe.call({
                                method: "craft_hr.events.leave_allocation.reopen_allocation",
                                args: {
                                    docname: frm.doc.name
                                },
                                callback: function(r) {
                                    if (!r.exc) {
                                        frm.reload_doc();
                                    }
                                }
                            });
                        }
                    );
                }, __('Actions'));
            }
        }
    }
});
