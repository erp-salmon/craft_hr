import frappe

def before_validate(doc, method):
    joining_date = frappe.db.get_value("Employee",doc.employee,"date_of_joining")
    doc.custom_working_days_from_joining = frappe.utils.date_diff(doc.end_date, joining_date)
    doc.custom_calendar_days = frappe.utils.date_diff(doc.end_date,doc.start_date)+1
    get_ot_from_overtime_sheet(doc)
    get_ot_from_attendance(doc)

def get_ot_from_overtime_sheet(doc):
    ot_data = frappe.db.sql("""
    select sum(ot) ot, sum(hot) hot, sum(food_allowance) food_allowance
    from `tabOvertime Hours`
    where docstatus = 1
    and employee = %s
    and date between %s and %s
    """,(doc.employee,doc.start_date,doc.end_date),as_dict=True)[0]
    doc.custom_ot = ot_data.ot
    doc.custom_holiday_ot = ot_data.hot

def get_ot_from_attendance(doc,method=None):
    doc.ot,doc.hot,doc.late_hours = frappe.db.sql("""
                                      SELECT
                                        SUM(ot) ot, SUM(hot) hot, SUM(late_hours) late_hours
                                      FROM
                                        `tabAttendance`
                                      WHERE
                                        employee = %s
                                      AND
                                        docstatus = 1
                                      AND
                                        attendance_date BETWEEN %s AND %s
                                      """,(doc.employee,doc.start_date,doc.end_date))[0]
    
import frappe
from frappe.utils import getdate

def on_salary_slip_submit(doc, event):
    process_deduction(doc, is_cancel=False)

def on_salary_slip_cancel(doc, event):
    process_deduction(doc, is_cancel=True)

def process_deduction(doc, is_cancel=False):
    slip_start = getdate(doc.start_date)
    slip_end = getdate(doc.end_date)

    additional_salaries = frappe.get_all(
        "Additional Salary",
        filters={
            "employee": doc.employee,
            "is_recurring": 1,
            "docstatus": 1,
            "ref_doctype": "Employee Advance",
        },
        fields=["name", "amount", "actual_amount", "deducted_amount", "balance_amount", "from_date", "to_date"]
    )

    for sal in additional_salaries:
        sal_from = getdate(sal.from_date)
        sal_to = getdate(sal.to_date)

        # ✅ Deduct only if slip month falls in Additional Salary period
        if slip_start < sal_from or slip_end > sal_to:
            continue

        monthly = float(sal.amount)
        deducted = float(sal.deducted_amount or 0)
        balance = float(sal.balance_amount or sal.actual_amount)

        if not is_cancel:
            deducted += monthly
        else:
            deducted -= monthly
            if deducted < 0:
                deducted = 0

        balance = float(sal.actual_amount) - deducted
        if balance < 0:
            balance = 0

        frappe.db.set_value("Additional Salary", sal.name, {
            "deducted_amount": deducted,
            "balance_amount": balance
        })

        # # ✅ Stop recurring when fully recovered
        # if balance == 0 and not is_cancel:
        #     frappe.db.set_value("Additional Salary", sal.name, "is_recurring", 0)
        #     frappe.db.set_value("Additional Salary", sal.name, "to_date", doc.end_date)

        # # ✅ Restart on cancel if balance > 0
        # if is_cancel and balance > 0:
        #     frappe.db.set_value("Additional Salary", sal.name, "is_recurring", 1)

    frappe.db.commit()
