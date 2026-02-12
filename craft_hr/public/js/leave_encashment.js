frappe.ui.form.on('Leave Encashment', {
    setup: function(frm) {
        frm.set_query('custom_salary_structure_assignment', function() {
            return {
                query: 'craft_hr.overrides.leave_encashment.get_salary_structure_assignment_query',
                filters: {
                    employee: frm.doc.employee,
                    encashment_date: frm.doc.encashment_date
                }
            };
        });
    },

    refresh: function(frm) {
        set_field_properties(frm);
    },

    onload: function(frm) {
        set_field_properties(frm);
    }
});

function set_field_properties(frm) {
    frappe.call({
        method: 'frappe.client.get_single_value',
        args: {
            doctype: 'Craft HR Settings',
            field: 'encashment_amount_method'
        },
        async: false,
        callback: function(r) {
            const amount_method = r.message || 'Auto';
            // Make encashment_amount editable only in Manual mode
            frm.set_df_property('encashment_amount', 'read_only', amount_method === 'Auto' ? 1 : 0);
            if (amount_method === 'Manual') {
                frm.set_df_property('encashment_amount', 'description', 'Enter encashment amount manually');
            }
        }
    });
}
