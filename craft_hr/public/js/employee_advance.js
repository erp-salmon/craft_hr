

frappe.ui.form.on("Employee Advance", {
    is_leave_salary: function(frm) {
        if (frm.doc.is_leave_salary) {
            frm.__original_advance_account = frm.doc.advance_account;

            if (frm.doc.company) {
                frappe.db.get_value("Company", frm.doc.company, "leave_salary_advance_account", (r) => {
                    if (r && r.leave_salary_advance_account) {
                        frm.set_value("advance_account", r.leave_salary_advance_account);
                    } else {
                        frappe.msgprint(__('No Leave Salary Advance Account set in Company {0}', [frm.doc.company]));
                    }
                });
            }
        } else {
            if (frm.__original_advance_account) {
                frm.set_value("advance_account", frm.__original_advance_account);
            }
        }
    }
});