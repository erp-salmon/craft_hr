# Copyright (c) 2024, Craftinteractive and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, flt
from frappe.model.mapper import get_mapped_doc
from frappe.utils import add_days, nowdate

class TicketAllocation(Document):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = frappe.get_single("Craft HR Settings")

    def validate(self, method=None):
        values = self.get_calculated()
        self.earned_days = values.get("earned_days")
        self.ticket_value_earned = values.get("ticket_value_earned")
        self.rounded_ticket_value_earned = values.get("rounded_ticket_value_earned")
        self.eligibility = values.get("eligibility")

    def on_update_after_submit(self, method=None):
        values = self.get_calculated()
        self.db_set({
            "earned_days": values.get("earned_days"),
            "ticket_value_earned": values.get("ticket_value_earned"),
            "rounded_ticket_value_earned": values.get("rounded_ticket_value_earned"),
            "eligibility": values.get("eligibility")
        })
        self.reload()

    def get_calculated(self):
        result = frappe._dict()
        date_diff = frappe.utils.date_diff(getdate(), getdate(self.posting_date))

        # Calculate the number of unpaid leave days
        unpaid_leave_days = self.get_unpaid_leave_days()

        # Subtract unpaid leave days from the total date difference
        effective_days = date_diff - unpaid_leave_days

        result["earned_days"] = abs(effective_days) + flt(self.opening) - flt(self.used_days)
        result["ticket_value_earned"] = flt(self.settings.per_day_amount) * result.get("earned_days")
        result["rounded_ticket_value_earned"] = int(result["ticket_value_earned"]) or 0
        result["eligibility"] = (
            "Eligible"
            if result["rounded_ticket_value_earned"] >= flt(self.settings.threshold_amount)
            else "Not Eligible"
        )
        return result

    def get_unpaid_leave_days(self):
        unpaid_leave_days = frappe.db.sql("""
            SELECT COUNT(*)
            FROM `tabAttendance` a
            LEFT JOIN `tabLeave Type` lt ON a.leave_type = lt.name
            WHERE a.employee = %s AND (
                (a.status = 'On Leave' AND lt.is_lwp = 1) OR
                a.status = 'Absent'
            ) AND a.attendance_date >= %s
        """, (self.employee, self.posting_date), as_dict=0)
        return unpaid_leave_days[0][0] if unpaid_leave_days and unpaid_leave_days[0][0] else 0

    def calculate_eligibility_date(self):
        if self.earned_days < 730:
            target_date = add_days(nowdate(), 730 - self.earned_days)
        else:
            target_date = add_days(self.posting_date, 730 + self.used_days)
        self.db_set("eligibility_date", target_date)


def daily_event():
    ticket_allocations = frappe.db.get_all(
        "Ticket Allocation", filters={"docstatus": 1}, pluck="name"
    )
    for allocation_name in ticket_allocations:
        allocation_doc = frappe.get_doc("Ticket Allocation", allocation_name)
        allocation_doc.on_update_after_submit()
        allocation_doc.calculate_eligibility_date()


@frappe.whitelist()
def ticket_application(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.run_method("set_missing_values")

    target_doc = get_mapped_doc(
        "Ticket Allocation",
        source_name,
        {
            "Ticket Allocation": {
                "doctype": "Ticket Application",
                "field_map": {
                    "employee": "employee",
                    "earned_days": "available_days"
                }
            },
        },
        target_doc,
        set_missing_values,
    )

    return target_doc
