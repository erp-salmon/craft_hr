frappe.ui.form.on("Additional Salary", {
    salary_component: function(frm) {
        update_reimbursement_amount(frm);
    },

    payroll_date: function(frm) {
        update_reimbursement_amount(frm);
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
                callback: function(res) {
                    if (res.message) {
                        frm.set_value("amount", res.message.amount);
                        frm.refresh_field("amount");
                    }
                }
            });
        }
    });
}
