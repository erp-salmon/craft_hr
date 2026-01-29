import frappe
from craft_hr.events.get_leaves import get_leaves, get_earned_leave


def validate(doc, method):
    # TODO: use is_earned_leave from inside leave type for this logic
    if doc.custom_is_earned_leave and doc.custom_leave_distribution_template:
        include_partial_months = frappe.db.get_single_value(
            "Craft HR Settings", "include_partial_months_in_earned_leave"
        ) or 0
        total_opening_leaves = get_leaves(
            doc.custom_date_of_joining,
            doc.from_date,
            doc.custom_leave_distribution_template,
            include_partial_months
        ) or 0
        doc.custom_used_leaves = total_opening_leaves - doc.custom_opening_leaves
        doc.custom_opening_used_leaves = total_opening_leaves - doc.custom_opening_leaves
        doc.new_leaves_allocated = doc.custom_opening_leaves
        doc.custom_available_leaves = doc.custom_opening_leaves

def before_submit(doc,method):
    if doc.custom_is_earned_leave:
        get_earned_leave(doc.employee)

#TODO: Make sure there is no leave application across the leave allocation after today date before closing

@frappe.whitelist()
def close_allocation(docname):
    # Check permission - only HR Manager can close manually
    if 'HR Manager' not in frappe.get_roles():
        frappe.throw("Only HR Manager can manually close leave allocations", frappe.PermissionError)

    doc = frappe.get_doc("Leave Allocation", docname)

    if doc.docstatus != 1:
        frappe.throw("Can only close submitted leave allocations")

    if doc.custom_status == 'Closed':
        frappe.throw("Leave Allocation is already closed")

    # Running get earned leave to ensure correct calculation of balance leave before closing
    get_earned_leave(doc.employee)
    doc.db_set("custom_status", "Closed")
    doc.db_set("to_date", frappe.utils.nowdate())
    frappe.msgprint(f"Leave Allocation {docname} has been closed", alert=True)


@frappe.whitelist()
def reopen_allocation(docname):
    """Manually reopen a leave allocation - restricted to HR Manager"""
    # Check permission - only HR Manager can reopen manually
    if 'HR Manager' not in frappe.get_roles():
        frappe.throw("Only HR Manager can manually reopen leave allocations", frappe.PermissionError)

    doc = frappe.get_doc("Leave Allocation", docname)

    if doc.docstatus != 1:
        frappe.throw("Can only reopen submitted leave allocations")

    if doc.custom_status != 'Closed':
        frappe.throw("Leave Allocation is not closed")

    # Check if there's a newer ongoing allocation
    newer_allocation_exists = frappe.db.exists('Leave Allocation', {
        'employee': doc.employee,
        'leave_type': doc.leave_type,
        'from_date': ['>', doc.from_date],
        'docstatus': 1,
        'custom_status': 'Ongoing'
    })

    if newer_allocation_exists:
        frappe.throw("Cannot reopen - a newer allocation exists for this leave type")

    # Check employee status
    emp_status, emp_relieving_date = frappe.db.get_value(
        'Employee', doc.employee, ['status', 'relieving_date']
    ) or (None, None)

    if emp_status in ('Left', 'Inactive'):
        frappe.throw(f"Cannot reopen - Employee status is '{emp_status}'")

    if emp_relieving_date:
        frappe.throw("Cannot reopen - Employee has a relieving date set")

    doc.db_set('custom_status', 'Ongoing')
    frappe.msgprint(f"Leave Allocation {docname} has been reopened", alert=True)
