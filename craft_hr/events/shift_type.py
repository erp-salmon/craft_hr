import frappe
import datetime
from frappe.utils import time_diff_in_hours
from datetime import timedelta

def before_validate(doc, method):
    manually_add = frappe.db.get_single_value("Craft HR Settings", "manually_add_shift_hours")

    if manually_add:
        if not doc.manual_shift_hours:
            frappe.throw("Please enter Manual Shift Hours since the setting is enabled.")
        shift_hours = doc.manual_shift_hours
    else:
        start = doc.start_time
        end = doc.end_time
        if isinstance(doc.start_time, str):
            start = datetime.datetime.strptime(doc.start_time, "%H:%M:%S")
            end = datetime.datetime.strptime(doc.end_time, "%H:%M:%S")
        if doc.is_night_shift:
            end += timedelta(hours=24)
        shift_hours = time_diff_in_hours(end, start)

    doc.db_set("shift_hours", shift_hours)
