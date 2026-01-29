import frappe
from dateutil.relativedelta import relativedelta

# Cache for leave distribution templates to avoid repeated DB calls
_template_cache = {}


def get_template_data(template_name):
    """Get template data with caching"""
    if template_name not in _template_cache:
        template = frappe.get_doc('Leave Distribution Template', template_name)
        month_array = {}
        cumulative_allocation = {}

        for row in template.leave_distribution:
            if row.end != 0:
                for i in range(row.start, row.end + 1, 1):
                    month_array[i] = row.monthly_allocation
            else:
                month_array[row.start] = row.monthly_allocation
                month_array[row.end] = row.monthly_allocation

        allocation = 0
        max_key = max(list(month_array.keys())) if month_array else 0
        for i in range(1, max_key + 1, 1):
            allocation = allocation + month_array.get(i, 0)
            cumulative_allocation[i] = allocation
        cumulative_allocation[0] = month_array.get(0, 0)

        _template_cache[template_name] = {
            'month_array': month_array,
            'cumulative_allocation': cumulative_allocation,
            'max_months': max(list(cumulative_allocation.keys())) if cumulative_allocation else 0,
            'max_month_key': max_key
        }

    return _template_cache[template_name]


def clear_template_cache():
    """Clear template cache - call when templates are updated"""
    global _template_cache
    _template_cache = {}


def get_leaves(date_of_joining, allocation_start_date, leave_distribution_template=None, include_partial_months=False):
    """
    Calculate earned leaves based on leave distribution template.

    Args:
        date_of_joining: Employee's date of joining
        allocation_start_date: Date to calculate leaves up to
        leave_distribution_template: Name of the template to use
        include_partial_months: If True, credit partial months with 15+ days

    Returns:
        float: Number of earned leaves
    """
    doj = frappe.utils.getdate(date_of_joining)
    alloc_date = frappe.utils.getdate(allocation_start_date)
    diff = relativedelta(alloc_date, doj)
    opening_months = diff.years * 12 + diff.months

    # Include partial month if setting enabled and 15+ days
    if include_partial_months and diff.days >= 15:
        opening_months += 1

    if opening_months < 0:
        frappe.throw("Leave Period from date should be after employee joining date")

    if opening_months == 0:
        return 0

    template_data = get_template_data(leave_distribution_template)
    cumulative_allocation = template_data['cumulative_allocation']
    max_months = template_data['max_months']
    max_month_key = template_data['max_month_key']

    if opening_months <= max_month_key:
        leaves = cumulative_allocation.get(opening_months, 0)
    else:
        leaves = cumulative_allocation[max_months] + cumulative_allocation[0] * (opening_months - max_months)

    return leaves


def get_earned_leave(employee=None):
    """
    Update earned leave allocations for employees.
    Optimized for performance with batch operations.

    Args:
        employee: Optional employee ID to update only their allocations
    """
    filters = {
        'docstatus': 1,
        'custom_leave_distribution_template': ['is', 'set'],
        'custom_status': "Ongoing"
    }
    if employee:
        filters['employee'] = employee

    # Fetch all required allocation data in one query
    allocations = frappe.db.get_all(
        'Leave Allocation',
        filters=filters,
        fields=[
            'name', 'employee', 'leave_type', 'from_date', 'to_date',
            'custom_date_of_joining', 'custom_leave_distribution_template',
            'custom_opening_used_leaves', 'custom_opening_leaves'
        ]
    )

    if not allocations:
        return

    # Get settings once
    include_partial_months = frappe.db.get_single_value(
        "Craft HR Settings", "include_partial_months_in_earned_leave"
    ) or 0

    # Get unique employees and fetch their data in batch
    employee_ids = list(set(a.employee for a in allocations))
    employee_data = {}
    for emp in frappe.db.get_all(
        'Employee',
        filters={'name': ['in', employee_ids]},
        fields=['name', 'status', 'relieving_date', 'date_of_joining']
    ):
        employee_data[emp.name] = emp

    # Get attendance counts in batch
    attendance_counts = {}
    for alloc in allocations:
        key = (alloc.employee, alloc.leave_type, alloc.from_date, alloc.to_date)
        if key not in attendance_counts:
            attendance_counts[key] = frappe.db.count('Attendance', {
                'employee': alloc.employee,
                'leave_type': alloc.leave_type,
                'docstatus': 1,
                'status': 'On Leave',
                'attendance_date': ['between', [alloc.from_date, alloc.to_date]]
            })

    today = frappe.utils.getdate()

    for alloc in allocations:
        emp = employee_data.get(alloc.employee)
        if not emp:
            continue

        # Skip inactive/left employees
        if emp.status not in ('Active', None):
            continue

        # Determine effective end date
        to_date = today
        if alloc.to_date < to_date:
            to_date = alloc.to_date

        # Cap at relieving date
        if emp.relieving_date and frappe.utils.getdate(emp.relieving_date) < to_date:
            to_date = frappe.utils.getdate(emp.relieving_date)

        # Use fresh joining date from Employee if available
        date_of_joining = emp.date_of_joining or alloc.custom_date_of_joining

        earned_leaves = get_leaves(
            date_of_joining,
            to_date,
            alloc.custom_leave_distribution_template,
            include_partial_months
        )

        key = (alloc.employee, alloc.leave_type, alloc.from_date, alloc.to_date)
        new_used_leaves = attendance_counts.get(key, 0)

        new_leaves_allocated = earned_leaves - (alloc.custom_opening_used_leaves or 0)
        custom_used_leaves = (alloc.custom_opening_used_leaves or 0) + new_used_leaves
        custom_available_leaves = new_leaves_allocated - new_used_leaves

        # Use db_set for better performance (avoids full document load and validation)
        frappe.db.set_value('Leave Allocation', alloc.name, {
            'new_leaves_allocated': new_leaves_allocated,
            'custom_used_leaves': custom_used_leaves,
            'custom_available_leaves': custom_available_leaves
        }, update_modified=False)

    # Commit the batch updates
    frappe.db.commit()
