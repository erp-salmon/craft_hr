frappe.ui.form.on('Leave Encashment', {
    refresh: function(frm) {
        set_field_properties(frm);
    },

    onload: function(frm) {
        set_field_properties(frm);
    }
});

function set_field_properties(frm) {
    // Get settings and set field properties
    frappe.call({
        method: 'frappe.client.get_single_value',
        args: {
            doctype: 'Craft HR Settings',
            field: 'encashment_days_method'
        },
        async: false,
        callback: function(r) {
            const days_method = r.message || 'Auto';
            // Make encashable_days editable only in Manual mode
            frm.set_df_property('encashable_days', 'read_only', days_method === 'Auto' ? 1 : 0);
            if (days_method === 'Manual') {
                frm.set_df_property('encashable_days', 'description', 'Enter encashable days manually');
            }
        }
    });

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
