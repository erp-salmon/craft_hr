import frappe

def validate(doc, method):
    payroll_entries = frappe.db.sql("""
        SELECT pe.name 
        FROM `tabPayroll Entry` pe
        JOIN `tabPayroll Employee Detail` ped ON ped.parent = pe.name
        WHERE ped.employee = %s
        AND pe.start_date <= %s AND pe.end_date >= %s
        AND pe.docstatus = 1
    """, (doc.employee, doc.from_date, doc.from_date), as_list=True)

    if payroll_entries:
        payroll_names = ", ".join(pe[0] for pe in payroll_entries)
        frappe.throw(
            f"Cannot amend the Salary Structure Assignment. A payroll entry ({payroll_names}) has already been processed for this period. "
        )
