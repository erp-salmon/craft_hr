import frappe
from craft_hr.events.get_leaves import get_earned_leave, get_leaves


def reset_leave_allocation():
    """
    Reset leave allocations that have expired with reset_allocation_on_expiry enabled.
    Creates new allocations for the next period with optional carry forward.
    """
    filters = {
        "reset_allocation_on_expiry": 1,
        "to_date": ["<=", frappe.utils.getdate()],
        "docstatus": 1,
        "custom_status": "Ongoing"
    }

    allocations = frappe.db.get_all(
        "Leave Allocation",
        filters=filters,
        fields=[
            'name', 'employee', 'leave_type', 'from_date', 'to_date',
            'custom_is_earned_leave', 'custom_leave_distribution_template',
            'custom_date_of_joining', 'reset_to', 'new_leaves_allocated',
            'custom_opening_leaves', 'custom_opening_used_leaves',
            'custom_used_leaves', 'custom_available_leaves', 'total_leaves_allocated'
        ]
    )

    if not allocations:
        return

    # Get settings once
    settings = frappe.get_single("Craft HR Settings")
    carry_forward = settings.reset_allocation_with_carry_forward or 0
    max_carry_forward = settings.max_carry_forward_leaves or 0
    proration_method = settings.earned_leave_proration_method or "Monthly"
    reset_to_date = settings.reset_allocation_to_date

    # Get employee data in batch
    employee_ids = list(set(a.employee for a in allocations))
    employee_data = {}
    for emp in frappe.db.get_all(
        'Employee',
        filters={'name': ['in', employee_ids]},
        fields=['name', 'status', 'relieving_date', 'date_of_joining']
    ):
        employee_data[emp.name] = emp

    # Check existing allocations in batch to prevent duplicates
    existing_allocations = set()
    for alloc in allocations:
        new_from_date = frappe.utils.add_days(alloc.to_date, 1)
        existing = frappe.db.exists("Leave Allocation", {
            "employee": alloc.employee,
            "leave_type": alloc.leave_type,
            "from_date": new_from_date,
            "docstatus": ["!=", 2]
        })
        if existing:
            existing_allocations.add(alloc.name)

    for alloc in allocations:
        emp = employee_data.get(alloc.employee)

        # Skip if employee data not found
        if not emp:
            frappe.db.set_value('Leave Allocation', alloc.name, 'custom_status', 'Closed', update_modified=False)
            continue

        # Skip inactive/left employees
        if emp.status not in ('Active', None):
            frappe.db.set_value('Leave Allocation', alloc.name, 'custom_status', 'Closed', update_modified=False)
            continue

        # Calculate new allocation dates
        new_from_date = frappe.utils.add_days(alloc.to_date, 1)
        # Use configured to_date if set and valid, otherwise add 1 year
        if reset_to_date and frappe.utils.getdate(reset_to_date) > new_from_date:
            new_to_date = frappe.utils.getdate(reset_to_date)
        else:
            new_to_date = frappe.utils.add_years(alloc.to_date, 1)

        # Skip if employee was relieved before new allocation period starts
        if emp.relieving_date and frappe.utils.getdate(emp.relieving_date) < new_from_date:
            frappe.db.set_value('Leave Allocation', alloc.name, 'custom_status', 'Closed', update_modified=False)
            continue

        # Skip if allocation already exists
        if alloc.name in existing_allocations:
            continue

        # Calculate unused leaves for carry forward
        unused_leaves = 0
        if carry_forward:
            # For earned leave allocations, calculate properly
            if alloc.custom_is_earned_leave and alloc.custom_leave_distribution_template:
                # Calculate total earned up to allocation end date
                date_of_joining = emp.date_of_joining or alloc.custom_date_of_joining
                total_earned = get_leaves(
                    date_of_joining,
                    alloc.to_date,
                    alloc.custom_leave_distribution_template,
                    proration_method=proration_method
                )
                # Unused = Total earned - Opening used - New used
                total_used = alloc.custom_used_leaves or 0
                unused_leaves = total_earned - total_used
            else:
                # Standard allocation: total_leaves_allocated - leaves_taken
                leaves_taken = frappe.db.sql("""
                    SELECT COALESCE(SUM(total_leave_days), 0)
                    FROM `tabLeave Application`
                    WHERE employee = %s
                    AND leave_type = %s
                    AND docstatus = 1
                    AND from_date >= %s
                    AND to_date <= %s
                """, (alloc.employee, alloc.leave_type, alloc.from_date, alloc.to_date))[0][0]
                unused_leaves = (alloc.total_leaves_allocated or 0) - leaves_taken

            # Apply max carry forward limit if set
            if max_carry_forward > 0 and unused_leaves > max_carry_forward:
                unused_leaves = max_carry_forward

            # Ensure non-negative
            unused_leaves = max(0, unused_leaves)

        # Create new allocation
        new_allocation = frappe.copy_doc(frappe.get_doc("Leave Allocation", alloc.name))
        new_allocation.from_date = new_from_date
        new_allocation.to_date = new_to_date
        new_allocation.carry_forward = carry_forward

        if alloc.custom_is_earned_leave and alloc.custom_leave_distribution_template:
            # For earned leave: start fresh with opening leaves as carry forward
            new_allocation.custom_opening_leaves = unused_leaves if carry_forward else 0
            new_allocation.custom_opening_used_leaves = 0  # Reset for new period
            new_allocation.new_leaves_allocated = unused_leaves if carry_forward else 0
            new_allocation.custom_used_leaves = 0
            new_allocation.custom_available_leaves = unused_leaves if carry_forward else 0
        else:
            # Standard allocation
            new_allocation.new_leaves_allocated = alloc.reset_to or 0
            if carry_forward:
                new_allocation.carry_forwarded_leaves = unused_leaves

        new_allocation.insert(ignore_permissions=True)
        new_allocation.submit()

        # Close old allocation
        frappe.db.set_value('Leave Allocation', alloc.name, 'custom_status', 'Closed', update_modified=False)

    frappe.db.commit()


def update_leave_allocations():
    """Update earned leave allocations daily"""
    get_earned_leave()


def close_expired_allocations():
    """
    Close allocations that have expired (to_date < today) and don't have reset_allocation_on_expiry.
    Only runs if setting is enabled.
    """
    # Check if auto-close is enabled
    auto_close_enabled = frappe.db.get_single_value(
        "Craft HR Settings", "auto_close_expired_allocations"
    )

    if not auto_close_enabled:
        return

    today = frappe.utils.getdate()

    # Use SQL for bulk update instead of loop
    frappe.db.sql("""
        UPDATE `tabLeave Allocation`
        SET custom_status = 'Closed', modified = NOW()
        WHERE docstatus = 1
        AND custom_status = 'Ongoing'
        AND to_date < %s
        AND (reset_allocation_on_expiry = 0 OR reset_allocation_on_expiry IS NULL)
    """, (today,))

    frappe.db.commit()
