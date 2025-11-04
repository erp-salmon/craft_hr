

// // // Copyright (c) 2025, craft@gmail.com and contributors
// // // For license information, please see license.txt

frappe.ui.form.on('Salary Increment', {
refresh: function(frm) {
    frm.set_query("employee", () => ({ filters: { "status": "Active" } }));

    if (!frm.is_new() && frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Add Salary'), function() {

            frappe.call({
                method: "craft_hr.craft_hr.doctype.salary_increment.salary_increment.get_latest_salary_structure",
                args: { employee: frm.doc.employee },
                callback: function(r) {

                    let latest_ss = r.message ? r.message.salary_structure : null;
                    let base_values = r.message || {};

                    let d = new frappe.ui.Dialog({
                        title: 'Add Salary Increment',
                        size: 'large',
                        fields: [
                            { fieldname: 'salary_increment', label: 'Salary Increment', fieldtype: 'Link', options: 'Salary Increment', read_only: 1, default: frm.doc.name },
                            { fieldname: 'employee', label: 'Employee', fieldtype: 'Link', options: 'Employee', read_only: 1, default: frm.doc.employee },
                            { fieldname: 'date', label: 'Increment Date', fieldtype: 'Date', default: frappe.datetime.get_today(), reqd: 1 },
                            { fieldname: 'salary_structure', label: 'Salary Structure', fieldtype: 'Link', options: 'Salary Structure', reqd: 1, default: latest_ss },

                            { fieldname: 'section1', fieldtype: 'Section Break' },

                            { fieldname: 'sc_basic', label: 'Basic', fieldtype: 'Currency', default: 0 },
                            { fieldname: 'sc_hra', label: 'HRA', fieldtype: 'Currency', default: 0 },
                            { fieldname: 'sc_transport', label: 'Transport Allowance', fieldtype: 'Currency', default: 0 },
                            { fieldname: 'sc_other', label: 'Other Allowance', fieldtype: 'Currency', default: 0 },
                            { fieldname: 'sc_mobile', label: 'Mobile Allowance', fieldtype: 'Currency', default: 0 },
                            { fieldname: 'sc_car', label: 'Car Allowance', fieldtype: 'Currency', default: 0 },

                            { fieldname: 'column2', fieldtype: 'Column Break' },

                            { fieldname: 'custom_leave_encashment_amount_per_day', label: 'Leave Encashment/Day', fieldtype: 'Currency', default: 0 },
                            { fieldname: 'sc_cola', label: 'Cost of Living Allowance', fieldtype: 'Currency', default: 0 },
                            { fieldname: 'holiday_ot_rate', label: 'Holiday OT Rate', fieldtype: 'Currency', default: 0 },
                            { fieldname: 'ot_rate', label: 'OT Rate', fieldtype: 'Currency', default: 0 },
                            { fieldname: 'sc_fuel', label: 'Fuel Allowance', fieldtype: 'Currency', default: 0 },
                            { fieldname: 'custom_pension_percentage', label: 'Pension %', fieldtype: "Percent", default: 0 },
                            { fieldname: 'leave_salary', label: 'Leave Salary', fieldtype: "Percent", default: 0 },

                            { fieldname: 'section2', fieldtype: 'Section Break' },
                            { fieldname: 'increment_amount', label: 'Increment Amount', fieldtype: 'Currency', read_only: 1 }
                        ],

                        primary_action_label: 'Save',
                        primary_action: function(data) {

                            if ((data.increment_amount || 0) <= 0) {
                                frappe.throw(__('Increment amount should be greater than zero'));
                                return;
                            }

                            let latest_ssa_from_date = r.message ? r.message.from_date : null;
                            if (latest_ssa_from_date && data.date < latest_ssa_from_date) {
                                frappe.throw(__('Increment date should be greater than the latest Salary Structure Assignment date.'));
                                return;
                            }

                            frappe.confirm(
                                __('Are you sure you want to submit this increment?'),
                                function() {
                                    frappe.call({
                                        method: "craft_hr.craft_hr.doctype.salary_increment.salary_increment.create_increment",
                                        args: { docname: frm.doc.name, data },
                                        callback: function(r) {
                                            if (!r.exc) {
                                                frappe.show_alert({ message: __("Increment added successfully"), indicator: "green" });
                                                frm.reload_doc();
                                            }
                                        }
                                    });
                                    d.hide();
                                }
                            );
                        }
                    });

                    function recalc_totals() {
                            let total = 0;
                            [
                                "sc_basic","sc_hra","sc_transport","sc_other",
                                "sc_mobile","sc_car","custom_leave_encashment_amount_per_day",
                                "sc_cola","holiday_ot_rate","ot_rate","sc_fuel"
                            ].forEach(k => {
                                total += (d.get_value(k) || 0);
                            });
                            d.set_value('increment_amount', total);
                        }

                        [
                            "sc_basic","sc_hra","sc_transport","sc_other",
                            "sc_mobile","sc_car","custom_leave_encashment_amount_per_day",
                            "sc_cola","holiday_ot_rate","ot_rate","sc_fuel"
                        ].forEach(key => {
                            d.fields_dict[key].df.onchange = () => recalc_totals();
                        });


                    recalc_totals();
                    d.show();
                }
            });
        });
    }

    if (frm.doc.docstatus === 1) {
        frm.fields_dict["increments"].grid.wrapper.find('.grid-add-row, .grid-add-multiple-rows').hide();
    }
},

    delete_component: function(frm) {
        if (!frm.doc.increments || frm.doc.increments.length === 0) {
            frappe.show_alert({ message: __('No Increments to delete'), indicator: 'orange' });
            return;
        }

        const lastIncrement = frm.doc.increments[frm.doc.increments.length - 1];

        if (!lastIncrement.increment_date) {
            frappe.show_alert({ message: __('The last Increment does not have an increment date.'), indicator: 'orange' });
            return;
        }

        frappe.db.get_value(
            'Salary Structure Assignment',
            { employee: frm.doc.employee, from_date: lastIncrement.increment_date, docstatus: 1 },
            'name',
            function(result) {
                if (result && result.name) {
                    frappe.throw(
                        __('Please cancel the linked Salary Structure Assignment before deleting the last row: <a href="/app/salary-structure-assignment/{0}" target="_blank">{0}</a>.', [result.name])
                    );
                } else {
                    frappe.confirm(
                        __('Are you sure you want to delete the last row?'),
                        function() {
                            frm.doc.increments.pop();
                            frm.dirty();
                            frm.save().then(() => {
                                frm.refresh_field('increments');
                                frappe.show_alert({ message: __('Row deleted successfully'), indicator: 'green' });
                            });
                        }
                    );
                }
            }
        );
    }
});