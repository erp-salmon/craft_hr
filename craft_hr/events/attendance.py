import frappe
from frappe.utils import (time_diff_in_hours)
from hrms.hr.utils import get_holiday_dates_for_employee
from craft_hr.events.get_leaves import get_earned_leave
import datetime
from datetime import timedelta

def on_cancel(doc, method):
    #TODO: condition to check if the leave type is earned leave
    get_earned_leave(doc.employee)

# Attendance On Submit: Will fetch the shift  details and based on that it'll calculate overtimte and HOT

def on_submit(doc, method=None):
    ot = hot = late_hours = 0

    is_holiday = len(get_holiday_dates_for_employee(doc.employee, doc.attendance_date, doc.attendance_date)) > 0

    if not doc.shift or not doc.working_hours:
        return

    (shift_end, shift_start, break_hours, enable_ot, enable_hot, shift_threshold, is_night_shift, shift_hours) = frappe.db.get_value(
        'Shift Type',
        doc.shift,
        ['end_time', 'start_time', 'break_hours', 'enable_ot', 'enable_hot', 'shift_threshold', 'is_night_shift', 'shift_hours']
    )

    if shift_threshold < 1:
        shift_threshold = 1

    if doc.working_hours <= shift_threshold:
        break_hours = 0

    if is_holiday and enable_hot:
        hot = doc.working_hours - break_hours
    elif not is_holiday and enable_ot:
        ot = doc.working_hours - shift_hours
        if ot < 0:
            late_hours = -ot
            ot = 0

    doc.db_set('shift_hours', shift_hours)
    doc.db_set('break_hours', break_hours)
    doc.db_set('ot', ot)
    doc.db_set('hot', hot)
    doc.db_set('late_hours', late_hours)
