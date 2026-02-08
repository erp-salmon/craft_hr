

frappe.ui.form.on("Company", {
    refresh: function(frm) {
        frm.set_query("leave_salary_advance_account", function() {
            return {
                filters: {
                    company: frm.doc.name,
                    is_group: 0,
                    root_type: "Asset",
                }
            };
        });
    }
});