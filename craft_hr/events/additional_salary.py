import frappe
from frappe.utils import getdate

@frappe.whitelist()
def get_deferred_leave_reimbursement_amount(employee, payroll_date):
    payroll_date = getdate(payroll_date)

    ssa = frappe.db.sql("""
        SELECT name FROM `tabSalary Structure Assignment`
        WHERE employee = %s AND from_date <= %s
        ORDER BY from_date DESC LIMIT 1
    """, (employee, payroll_date), as_dict=True)

    if not ssa:
        frappe.throw(f"No Salary Structure Assignment found for {employee} on or before {payroll_date}")

    row = frappe.db.get_value("Salary Structure Assignment", ssa[0].name, [
        "sc_basic", "sc_hra", "sc_transport", "sc_cola", "sc_other",
        "sc_fuel", "sc_mobile", "sc_car"
    ], as_dict=True)

    total_component = sum([
        row.get("sc_basic") or 0,
        row.get("sc_hra") or 0,
        row.get("sc_transport") or 0,
        row.get("sc_cola") or 0,
        row.get("sc_other") or 0,
        row.get("sc_fuel") or 0,
        row.get("sc_mobile") or 0,
        row.get("sc_car") or 0
    ])

    per_day_salary = (total_component * 12) / 365

    leave_days = frappe.db.sql("""
        SELECT SUM(amount / (%s)) as total_days
        FROM `tabAdditional Salary`
        WHERE employee = %s
        AND salary_component IN (
            SELECT name FROM `tabSalary Component`
            WHERE type = 'Deduction' AND custom_is_deferred_leave_component = 1
        )
        AND ref_doctype = 'Leave Application'
        AND (custom_deferred_payment_reimbursed IS NULL OR custom_deferred_payment_reimbursed = 0)
        AND payroll_date <= %s
    """, (per_day_salary, employee, payroll_date), as_dict=True)

    total_days = round(leave_days[0]["total_days"] or 0, 2)
    total_amount = round(per_day_salary * total_days, 2)

    return {
        "amount": total_amount,
        "days": total_days
    }




def mark_deductions_as_reimbursed(doc, method):
    if not doc.salary_component:
        return

    is_reimbursement = frappe.db.get_value(
        "Salary Component", doc.salary_component, "custom_is_deferred_reimbursement_component"
    )

    if not is_reimbursement:
        return

    deduction_components = frappe.db.get_all("Salary Component", 
        filters={"custom_is_deferred_leave_component": 1, "type": "Deduction"},
        pluck="name"
    )

    if not deduction_components:
        return

    # Only consider Additional Salary records with payroll_date <= current Salary Slip payroll_date
    deductions = frappe.get_all("Additional Salary",
        filters={
            "employee": doc.employee,
            "salary_component": ["in", deduction_components],
            "ref_doctype": "Leave Application",
            "custom_deferred_payment_reimbursed": ["!=", 1],
            "docstatus": 1,
            "payroll_date": ["<=", doc.payroll_date]
        },
        pluck="name"
    )

    for name in deductions:
        deduction_doc = frappe.get_doc("Additional Salary", name)
        deduction_doc.db_set("custom_deferred_payment_reimbursed", 1)




def unmark_deductions_as_reimbursed(doc, method):
    if not doc.salary_component:
        return

    is_reimbursement = frappe.db.get_value(
        "Salary Component", doc.salary_component, "custom_is_deferred_reimbursement_component"
    )

    if not is_reimbursement:
        return

    deduction_components = frappe.db.get_all("Salary Component", 
        filters={"custom_is_deferred_leave_component": 1, "type": "Deduction"},
        pluck="name"
    )

    if not deduction_components:
        return

    # Only revert reimbursements for Additional Salary within this payroll_date
    deductions = frappe.get_all("Additional Salary",
        filters={
            "employee": doc.employee,
            "salary_component": ["in", deduction_components],
            "ref_doctype": "Leave Application",
            "custom_deferred_payment_reimbursed": 1,
            "docstatus": 1,
            "payroll_date": ["<=", doc.payroll_date]
        },
        pluck="name"
    )

    for name in deductions:
        deduction_doc = frappe.get_doc("Additional Salary", name)
        deduction_doc.db_set("custom_deferred_payment_reimbursed", 0)



@frappe.whitelist()
def update_recovery_dates(docname, new_from, new_to):
    doc = frappe.get_doc("Additional Salary", docname)

    doc.db_set("from_date", new_from)
    doc.db_set("to_date", new_to)

    balance = float(doc.actual_amount) - float(doc.deducted_amount or 0)

    # if balance <= 0:
    #     doc.db_set("amount", 0)
    #     return

    start = getdate(new_from)
    end = getdate(new_to)
    months = ((end.year - start.year) * 12) + (end.month - start.month) + 1

    if months < 1:
        months = 1

    new_monthly = balance / months

    doc.db_set("amount", round(new_monthly, 2))
    doc.db_set("balance_amount", balance)

    frappe.db.commit()
