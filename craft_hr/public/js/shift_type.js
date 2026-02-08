

frappe.ui.form.on('Shift Type', {
    refresh: function(frm) {
        frappe.db.get_single_value('Craft HR Settings', 'manually_add_shift_hours')
            .then(value => {
                if (value) {
                    frm.set_df_property('manual_shift_hours', 'hidden', 0);
                } else {
                    frm.set_df_property('manual_shift_hours', 'hidden', 1);
                }
            });
    }
});
