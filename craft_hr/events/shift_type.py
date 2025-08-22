import frappe
import datetime
from frappe.utils import time_diff_in_hours
from datetime import timedelta

def before_validate(doc, method):
    manually_add = frappe.db.get_single_value("Craft HR Settings", "manually_add_shift_hours")

    if manually_add:
        if doc.manual_shift_hours:
            shift_hours = doc.manual_shift_hours
        else:
            start = doc.start_time
            end = doc.end_time
            if isinstance(start, str):
                start = datetime.datetime.strptime(start, "%H:%M:%S")
                end = datetime.datetime.strptime(end, "%H:%M:%S")
            if doc.is_night_shift:
                end += timedelta(hours=24)
            shift_hours = time_diff_in_hours(end, start)
    else:
        start = doc.start_time
        end = doc.end_time
        if isinstance(start, str):
            start = datetime.datetime.strptime(start, "%H:%M:%S")
            end = datetime.datetime.strptime(end, "%H:%M:%S")
        if doc.is_night_shift:
            end += timedelta(hours=24)
        shift_hours = time_diff_in_hours(end, start)

    doc.db_set("shift_hours", shift_hours)
