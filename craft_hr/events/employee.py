import frappe


def on_update(doc, method):
    """Handle leave allocation status when employee status/relieving_date changes"""
    # Check if auto-close is enabled in settings
    auto_close_enabled = frappe.db.get_single_value(
        "Craft HR Settings", "auto_close_on_employee_separation"
    )

    if not auto_close_enabled:
        return

    old_doc = doc.get_doc_before_save()
    if not old_doc:
        return

    status_changed = old_doc.status != doc.status
    relieving_date_changed = old_doc.relieving_date != doc.relieving_date

    if not status_changed and not relieving_date_changed:
        return

    # Employee deactivated or relieved - close ongoing allocations
    if doc.status in ('Left', 'Inactive') or doc.relieving_date:
        close_employee_allocations(doc.name, doc.relieving_date)

    # Employee reactivated (rollback scenario) - reopen valid allocations
    elif old_doc.status in ('Left', 'Inactive') and doc.status == 'Active' and not doc.relieving_date:
        reopen_employee_allocations(doc.name)


def close_employee_allocations(employee, relieving_date=None):
    """Close ongoing leave allocations for an employee (called automatically on employee update)"""
    filters = {
        'employee': employee,
        'docstatus': 1,
        'custom_status': 'Ongoing'
    }

    allocations = frappe.db.get_all('Leave Allocation', filters=filters, pluck='name')

    for allocation_name in allocations:
        allocation = frappe.get_doc('Leave Allocation', allocation_name)

        # If relieving date is set, only close if allocation period covers or exceeds relieving date
        if relieving_date:
            if allocation.from_date <= frappe.utils.getdate(relieving_date):
                allocation.db_set('custom_status', 'Closed')
        else:
            # Status changed to Left/Inactive without relieving date - close all ongoing
            allocation.db_set('custom_status', 'Closed')


def reopen_employee_allocations(employee):
    """Reopen leave allocations for an employee who was reactivated (rollback scenario)"""
    today = frappe.utils.getdate()

    # Find closed allocations that are still within valid period
    filters = {
        'employee': employee,
        'docstatus': 1,
        'custom_status': 'Closed',
        'from_date': ['<=', today],
        'to_date': ['>=', today]
    }

    allocations = frappe.db.get_all('Leave Allocation', filters=filters, pluck='name')

    for allocation_name in allocations:
        # Check if there's a newer allocation for the same leave type (don't reopen if replaced)
        allocation = frappe.get_doc('Leave Allocation', allocation_name)

        newer_allocation_exists = frappe.db.exists('Leave Allocation', {
            'employee': employee,
            'leave_type': allocation.leave_type,
            'from_date': ['>', allocation.from_date],
            'docstatus': 1,
            'custom_status': 'Ongoing'
        })

        if not newer_allocation_exists:
            allocation.db_set('custom_status', 'Ongoing')
            frappe.msgprint(
                f"Leave Allocation {allocation_name} reopened for {employee}",
                alert=True
            )
