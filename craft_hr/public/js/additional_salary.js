frappe.ui.form.on("Additional Salary", {
    salary_component: function (frm) {
        update_reimbursement_amount(frm);
    },

    payroll_date: function (frm) {
        update_reimbursement_amount(frm);
    },
    refresh(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.is_recurring && frm.doc.ref_doctype === "Employee Advance") {
            frm.add_custom_button("Update Schedule", () => {
                show_update_schedule_dialog(frm);
            });
        }
    },
    is_recurring: function (frm) {
        if (frm.doc.is_recurring && frm.doc.ref_doctype === "Employee Advance" && frm.doc.ref_docname) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Employee Advance",
                    name: frm.doc.ref_docname
                },
                callback: function (r) {
                    if (r.message) {
                        let paid = r.message.paid_amount || 0;
                        let claimed = r.message.claimed_amount || 0;

                        let actual = paid - claimed;

                        frm.set_value("actual_amount", actual);
                        frm.refresh_field("actual_amount");
                    }
                }
            });
        }
    },
    from_date(frm) {
        frm.trigger("calculate_monthly_amount");
    },

    to_date(frm) {
        frm.trigger("calculate_monthly_amount");
    },
    calculate_monthly_amount(frm) {
        if (
            frm.doc.is_recurring &&
            frm.doc.from_date &&
            frm.doc.to_date &&
            frm.doc.actual_amount
        ) {
            let months = count_unique_months(frm.doc.from_date, frm.doc.to_date);

            if (months > 0) {
                let monthly_amount = frm.doc.actual_amount / months;
                frm.set_value("amount", monthly_amount);
            }
        }
    }
});

function update_reimbursement_amount(frm) {
    if (!frm.doc.salary_component || !frm.doc.employee || !frm.doc.payroll_date) return;

    frappe.db.get_value("Salary Component", frm.doc.salary_component, [
        "type",
        "custom_is_deferred_reimbursement_component"
    ]).then(r => {
        const data = r.message;

        if (data && data.type === "Earning" && data.custom_is_deferred_reimbursement_component) {
            frappe.call({
                method: "craft_hr.events.additional_salary.get_deferred_leave_reimbursement_amount",
                args: {
                    employee: frm.doc.employee,
                    payroll_date: frm.doc.payroll_date
                },
                callback: function (res) {
                    if (res.message) {
                        frm.set_value("amount", res.message.amount);
                        frm.refresh_field("amount");
                    }
                }
            });
        }
    });
}
function count_unique_months(from_date, to_date) {
    let start = new Date(from_date);
    let end = new Date(to_date);

    let count = 0;

    while (start <= end) {
        count++;
        start.setMonth(start.getMonth() + 1);
        start.setDate(1);
    }

    return count;
}
function show_update_schedule_dialog(frm) {
    const d = new frappe.ui.Dialog({
        title: "Update Recovery Schedule",
        fields: [
            {
                fieldname: "new_from_date",
                label: "New From Date",
                fieldtype: "Date",
                reqd: 1,
                default: frm.doc.from_date
            },
            {
                fieldname: "new_to_date",
                label: "New To Date",
                fieldtype: "Date",
                reqd: 1,
                default: frm.doc.to_date
            }
        ],
        primary_action_label: "Update",
        primary_action(values) {
            let current_from_date = frm.doc.from_date;
            let new_from_date = values.new_from_date;
            let current_to_date = frm.doc.to_date;
            let new_to_date = values.new_to_date;

            let from_month_changed =
                getYearMonth(current_from_date) !== getYearMonth(new_from_date);

            let to_month_changed =
                getYearMonth(current_to_date) !== getYearMonth(new_to_date);

            if (from_month_changed || to_month_changed) {
                frappe.call({
                    method: "craft_hr.events.additional_salary.update_recovery_dates",
                    args: {
                        docname: frm.doc.name,
                        new_from: values.new_from_date,
                        new_to: values.new_to_date
                    },
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.msgprint("Schedule updated.");
                            frm.reload_doc();
                            d.hide();
                        }
                    }
                });
            } else {
                frappe.throw(
                    __('No month change detected. Please change From Month or To Month to update the schedule.')
                );
            }

        }
    });

    d.show();
}

// Convert to YYYY-MM for safe comparison
const getYearMonth = (date) => {
    return frappe.datetime.str_to_obj(date).getFullYear() + '-' +
        frappe.datetime.str_to_obj(date).getMonth();
};