import frappe
from craft_hr.events.get_leaves import get_leaves, get_earned_leave

def validate(doc,method):
    # TODO: use is_earned_leave from inside leave type for this logic
    if doc.custom_is_earned_leave and doc.custom_leave_distribution_template:
        total_opening_leaves = get_leaves(doc.custom_date_of_joining,doc.from_date, doc.custom_leave_distribution_template) or 0
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
    doc = frappe.get_doc("Leave Allocation", docname)
    #Running get earned leave to ensure correct calculation of balance leave before closing
    get_earned_leave(doc.employee)
    doc.db_set("custom_status", "Closed")
    doc.db_set("to_date", frappe.utils.nowdate())
