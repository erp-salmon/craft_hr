import frappe
from craft_hr.events.get_leaves import get_earned_leave
from datetime import datetime, timedelta
from frappe.utils import getdate, flt, get_last_day, get_first_day, date_diff, add_days
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on


def is_leap_year(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def days_in_year(year):
    return 366 if is_leap_year(year) else 365

def on_submit(doc, method):
    # TODO: condition to check if the leave type is earned leave
    get_earned_leave(doc.employee)

def validate(doc, method):
    # leave_balance = get_leave_balance_on(
    #     employee=self.employee,
    #     date=self.from_date,
    #     to_date=self.to_date,
    #     leave_type=self.leave_type,
    #     consider_all_leaves_in_the_allocation_period=1
    # )

    # if leave_balance:
    #     leave_type_doc = frappe.get_doc("Leave Type", self.leave_type)
        
    #     if leave_type_doc.is_earned_leave and leave_type_doc.earned_leave_frequency == 'Monthly':
    #         leave_policy_assignment = frappe.get_value("Leave Policy Assignment", {"employee": self.employee}, "leave_policy")
            
    #         if leave_policy_assignment:
    #             leave_policy_doc = frappe.get_doc("Leave Policy", leave_policy_assignment)

    #             annual_allocation = None
    #             for detail in leave_policy_doc.leave_policy_details:
    #                 if detail.leave_type == self.leave_type:
    #                     annual_allocation = detail.annual_allocation
    #                     break

    #             if annual_allocation:
    #                 to_date = datetime.strptime(self.to_date, '%Y-%m-%d')
    #                 today = datetime.today()

    #                 total_months = (to_date.year - today.year) * 12 + to_date.month - today.month

    #                 additional_leave = (annual_allocation / 12) * total_months

    #                 self.custom_leave = additional_leave

    #                 eligible_leave = leave_balance + additional_leave

    #                 self.leave_balance = eligible_leave

    #                 if self.total_leave_days > eligible_leave:
    #                     frappe.msgprint(
    #                         _('Your total leave days exceed the eligible leave till {0}.').format(
    #                             frappe.utils.formatdate(self.to_date)
    #                         ),
    #                         title=_('Leave Balance Exceeded'),
    #                         indicator='orange'
    #                     )
    #         else:
    #             frappe.msgprint(
    #                 ('No leave policy assignment found for the employee.'),
    #                 title=('Leave Policy Error'),
    #                 indicator='red'
    #             )



    query = """
    SELECT 
        sa.salary_structure,
        sa.sc_basic,
        sa.sc_hra,
        sa.leave_salary,
        sa.from_date,
        COALESCE(
            (SELECT MIN(next_sa.from_date) 
             FROM `tabSalary Structure Assignment` next_sa 
             WHERE next_sa.employee = sa.employee 
               AND next_sa.from_date > sa.from_date AND next_sa.docstatus = 1),
            %(to_date)s
        ) AS to_date
    FROM 
        `tabSalary Structure Assignment` sa
    WHERE 
        sa.employee = %(employee)s
        AND sa.from_date <= %(to_date)s
        AND sa.from_date IS NOT NULL
        AND sa.docstatus = 1
    """

    if frappe.get_value("Leave Type", doc.leave_type, "calculate_leave_salary") == 1:
        salary_structures = frappe.db.sql(query, {
            'employee': doc.employee,
            'from_date': doc.from_date,
            'to_date': doc.to_date
        }, as_dict=True)
        total_prorated_base = 0

        for structure in salary_structures:
            # Calculate the effective date range
            effective_from_date = max(frappe.utils.getdate(structure.from_date), frappe.utils.getdate(doc.from_date))
            effective_to_date = min(frappe.utils.getdate(structure.to_date), frappe.utils.getdate(doc.to_date))

            # Calculate the number of active days within the range
            active_days = (effective_to_date - effective_from_date).days + 1
            if active_days > 0:
                leave_salary_percentage = structure.leave_salary / 100
                year_days = days_in_year(effective_from_date.year)
                proprated_base = ((((structure.sc_basic + structure.sc_hra) * 12) * leave_salary_percentage) / year_days) * active_days
                total_prorated_base += proprated_base

        doc.custom_leave_salary = total_prorated_base


def create_deferred_leave_additional_salary(doc, method):
    if not doc.leave_type or not doc.total_leave_days:
        return

    is_deferred = frappe.db.get_value("Leave Type", doc.leave_type, "custom_is_deferred_leave")
    if not is_deferred:
        return

    component = frappe.db.get_value("Salary Component", {
        "custom_is_deferred_leave_component": 1,
        "type": "Deduction",
        "disabled": 0
    }, "name")

    if not component:
        frappe.throw("No Deduction Salary Component found with 'Is Deferred Leave Component' enabled.")

    from_date = getdate(doc.from_date)
    to_date = getdate(doc.to_date)
    employee = doc.employee

    # Get employee holiday list
    holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")
    holiday_dates = []
    if holiday_list:
        holiday_dates = frappe.db.get_all("Holiday", filters={"parent": holiday_list}, pluck="holiday_date")
        holiday_dates = [getdate(d) for d in holiday_dates]

    # Group leave by month
    current = from_date
    while current <= to_date:
        month_start = get_first_day(current)
        month_end = get_last_day(current)
        period_start = max(from_date, month_start)
        period_end = min(to_date, month_end)

        # Get salary structures during this month period
        ssa_list = frappe.db.sql("""
            SELECT name, from_date
            FROM `tabSalary Structure Assignment`
            WHERE employee = %s AND from_date <= %s
            AND docstatus =1
            ORDER BY from_date ASC
        """, (employee, period_end), as_dict=True)

        if not ssa_list:
            frappe.throw(f"No Salary Structure Assignment found for employee {employee} on or before {period_end}")

        # Append end date to calculate duration for each SSA
        for i in range(len(ssa_list)):
            ssa_list[i]["end_date"] = ssa_list[i+1]["from_date"] if i+1 < len(ssa_list) else period_end + timedelta(days=1)

        # For each SSA, calculate leave days within its range
        total_amount = 0
        for ssa in ssa_list:
            ssa_start = max(period_start, getdate(ssa["from_date"]))
            ssa_end = min(period_end, getdate(ssa["end_date"]) - timedelta(days=1))
            if ssa_start > ssa_end:
                continue

            working_days = count_working_days(ssa_start, ssa_end, holiday_dates)
            if working_days <= 0:
                continue

            component_row = frappe.db.get_value("Salary Structure Assignment", ssa["name"], [
                "sc_basic", "sc_hra", "sc_transport", "sc_cola", "sc_other",
                "sc_fuel", "sc_mobile", "sc_car"
            ], as_dict=True)

            total_component = sum([
                component_row.get("sc_basic") or 0,
                component_row.get("sc_hra") or 0,
                component_row.get("sc_transport") or 0,
                component_row.get("sc_cola") or 0,
                component_row.get("sc_other") or 0,
                component_row.get("sc_fuel") or 0,
                component_row.get("sc_mobile") or 0,
                component_row.get("sc_car") or 0
            ])

            per_day = (total_component * 12) / days_in_year(ssa_start.year)
            total_amount += per_day * working_days

        if total_amount > 0:
            payroll_date = period_end
            _create_additional_salary(employee, component, total_amount, payroll_date, doc)

        current = get_first_day(add_days(current, 32))  # move to next month

    frappe.msgprint("Deferred Leave Additional Salary created.", alert=True)


def count_working_days(start, end, holidays):
    days = 0
    current = start
    while current <= end:
        if current not in holidays:
            days += 1
        current = add_days(current, 1)
    return days


def _create_additional_salary(employee, component, amount, payroll_date, doc):
    additional_salary = frappe.new_doc("Additional Salary")
    additional_salary.update({
        "employee": employee,
        "salary_component": component,
        "amount": round(amount, 2),
        "payroll_date": payroll_date,
        "overwrite_salary_structure_amount": 1,
        "ref_doctype": "Leave Application",
        "ref_docname": doc.name
    })
    additional_salary.insert()
    additional_salary.submit()




def cancel_linked_additional_salary(doc, method):
    additional_salaries = frappe.get_all("Additional Salary", 
        filters={
            "ref_doctype": "Leave Application",
            "ref_docname": doc.name,
            "docstatus": 1
        },
        pluck="name"
    )

    for name in additional_salaries:
        additional_salary = frappe.get_doc("Additional Salary", name)
        additional_salary.cancel()

    if additional_salaries:
        frappe.msgprint(
            "The linked Additional Salary has been cancelled.",
            alert=True
        )


def delete_deferred_leave_additional_salary(doc, method):
    additional_salary = frappe.get_all("Additional Salary", filters={
        "ref_doctype": "Leave Application",
        "ref_docname": doc.name,
        "docstatus": ("=", 2)
    })

    for salary in additional_salary:
        doc_to_delete = frappe.get_doc("Additional Salary", salary.name)
        doc_to_delete.delete()