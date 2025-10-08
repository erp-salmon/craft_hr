// Copyright (c) 2025, Craftinteractive and contributors
// For license information, please see license.txt

// Copyright (c) 2024, Craft Interactive and contributors
// For license information, please see license.txt


frappe.ui.form.on("Accommodation Transfer Form", {
    refresh: function(frm) {
        frm.set_query("to_floor_no", function() {
            return {
                filters: {
                    building_name: frm.doc.to_building_name
                }
            }
        });
        frm.set_query("to_room_no", function() {
            return {
                filters: {
                    floor_no: frm.doc.to_floor_no
                }
            }
        });

        frm.set_query("to_bed_no", function() {
            return {
                filters: {
                    room_no: frm.doc.to_room_no
                }
            }
        });
    },
});