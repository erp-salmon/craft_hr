
frappe.ui.form.on("Payroll Entry", {
    refresh: function(frm) {
        if(frm.doc.salary_slips_created && frm.doc.status == 'Submitted') {
            // custom buttons
            frm.add_custom_button(__('Download SIF'), function () {
                frappe.call({
                    method: 'craft_hr.api.get_sif_details.get_sif_details',
                    args: {
                        'employee': frm.doc.employee,
                        'pe': frm.doc.name,
                        'company':frm.doc.company
                    },
                    callback: function(r) {
                        if(!r.exc && r.message){
                            const out = r.message[0]
                            downloadsif(out, null, r.message[1]);          
                        }
                    }
                }); 
            });
        }
    },
});

frappe.provide("frappe.tools");

function downloadsif (data, roles, title) {
    if (roles && roles.length && !has_common(roles, roles)) {
        frappe.msgprint(
            __("Export not allowed. You need {0} role to export.", [frappe.utils.comma_or(roles)])
        );
        return;
    }

    var filename = title + ".sif";
    var csv_data = to_sif(data);
    var a = document.createElement("a");

    if ("download" in a) {
        // Used Blob object, because it can handle large files
        var blob_object = new Blob([csv_data], { type: "text/sif;charset=UTF-8" });
        a.href = URL.createObjectURL(blob_object);
        a.download = filename;
    } else {
        // use old method
        a.href = "data:attachment/sif," + encodeURIComponent(csv_data);
        a.download = filename;
        a.target = "_blank";
    }

    document.body.appendChild(a);
    a.click();

    document.body.removeChild(a);
};

function to_sif (data) {
    var res = [];
    $.each(data, function (i, row) {
        row = $.map(row, function (col) {
            if (col === null || col === undefined) col = "";
            return typeof col === "string"
                ? $("<i>").html(col.replace(/"/g, '""')).text()
                : col;
        });
        res.push(row.join(","));
    });
    return res.join("\n");
};