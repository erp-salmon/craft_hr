import frappe

def get_leaves(date_of_joining, allocation_start_date, leave_distribution_template=None):
    opening_months = round(frappe.utils.date_diff(allocation_start_date, date_of_joining)/365 * 12)
    if opening_months<0:
        frappe.throw("Leave Period from date should be after employee joining date")
    month_array = {}
    cumulative_allocation = {}    
    template = frappe.get_doc('Leave Distribution Template',leave_distribution_template)
    for row in template.leave_distribution:
        if row.end != 0:
            n = 0
            for i in range(row.start,row.end+1,1):
                month_array[i] = row.monthly_allocation
        else:
            month_array[row.start] = row.monthly_allocation
            month_array[row.end] =  row.monthly_allocation
    
    allocation = 0
    for i in range(1,max(list(month_array.keys()))+1,1):
        allocation = allocation + month_array[i]
        cumulative_allocation[i] = allocation
    cumulative_allocation[0] = month_array[0]
    max_months = max(list(cumulative_allocation.keys()))
    leaves = 0
    if opening_months <= max(list(month_array.keys())):
        leaves = cumulative_allocation[opening_months]
    else:
        leaves = cumulative_allocation[max_months] + cumulative_allocation[0] * (opening_months - max_months)
    if opening_months==0:
        leaves=0
    return leaves

def get_earned_leave(employee=None):
    filters = {
        'docstatus':1,
        'custom_leave_distribution_template':['is','set'],
        'custom_status':"Ongoing"
    }
    if employee:
        filters['employee'] = employee
    for la in frappe.db.get_list('Leave Allocation', filters):
        doc = frappe.get_doc('Leave Allocation', la.name)
        to_date = frappe.utils.getdate()
        if doc.to_date < to_date:
            to_date = doc.to_date
        earned_leaves = get_leaves(doc.custom_date_of_joining, to_date, doc.custom_leave_distribution_template)
        new_used_leaves = frappe.db.count('Attendance',{'employee':doc.employee,'leave_type':doc.leave_type,'docstatus':1,'attendance_date':['between',[doc.from_date,doc.to_date]]})
        doc.new_leaves_allocated = earned_leaves - doc.custom_opening_used_leaves
        doc.custom_used_leaves = doc.custom_opening_used_leaves + new_used_leaves
        doc.custom_available_leaves = doc.new_leaves_allocated - new_used_leaves
        doc.save()