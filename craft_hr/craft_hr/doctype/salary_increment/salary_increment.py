# # Copyright (c) 2024, Craftinteractive and contributors
# # For license information, please see license.txt


import frappe
import json
from frappe.database.database import getdate
from frappe.model.document import Document
class SalaryIncrement(Document):
    component_fields = [
        "sc_basic", "sc_hra", "sc_transport","sc_other", "sc_mobile",
        "sc_car", "custom_leave_encashment_amount_per_day", "sc_cola",
        "holiday_ot_rate", "ot_rate","sc_fuel","custom_pension_percentage",
        "leave_salary"
    ]

    exclude_from_sum = ["custom_pension_percentage", "leave_salary"]

    def validate(self):
        if not self.employee:
            frappe.throw("Employee is required")

        if not self.components:
            ssa = frappe.db.get_all(
                "Salary Structure Assignment",
                filters={"employee": self.employee, "docstatus": 1},
                fields=["name", "from_date", "salary_structure"] + self.component_fields,
                order_by="from_date desc",
                limit_page_length=1
            )
            if ssa:
                ssa = ssa[0]
                first_row = self.append("components", {})
                for f in self.component_fields:
                    first_row.set(f, ssa.get(f) or 0)
                first_row.increment_date = ssa.get("from_date")
                first_row.salary_structure = ssa.get("salary_structure")
            else:
                frappe.msgprint(f"No Salary Structure Assignment found for employee {self.employee}.")

        for row in self.components:
            row.net_amount = sum(
                (getattr(row, f, 0) or 0)
                for f in self.component_fields
                if f not in self.exclude_from_sum
            )

        for row in self.increments:
            row.increment_amount = sum(
                (getattr(row, f, 0) or 0)
                for f in self.component_fields
                if f not in self.exclude_from_sum
            )

            latest_ssa = frappe.get_all(
                "Salary Structure Assignment",
                filters={"employee": self.employee, "docstatus": 1},
                fields=self.component_fields,
                order_by="from_date desc",
                limit_page_length=1
            )
            latest_total = 0
            if latest_ssa:
                latest_ssa = latest_ssa[0]
                latest_total = sum(
                    latest_ssa.get(f, 0)
                    for f in self.component_fields
                    if f not in self.exclude_from_sum
                )

            row.net_amount = latest_total + row.increment_amount



    def on_submit(self):
        latest_ssa = frappe.db.get_all(
            "Salary Structure Assignment",
            filters={"employee": self.employee, "docstatus": 1},
            fields=["name", "from_date", "salary_structure"] + self.component_fields,
            order_by="from_date desc",
            limit_page_length=1
        )

        if not latest_ssa:
            return

        latest_ssa = latest_ssa[0]

        if not self.increments:
            frappe.throw("No increments found to create a new Salary Structure Assignment")

        inc_row = sorted(self.increments, key=lambda r: getdate(r.increment_date))[0]

        if getdate(inc_row.increment_date) <= getdate(latest_ssa.from_date):
            inc_date_str = getdate(inc_row.increment_date).strftime("%d-%m-%Y")
            ssa_date_str = getdate(latest_ssa.from_date).strftime("%d-%m-%Y")
            frappe.throw(
                f"Increment date {inc_date_str} must be greater than the "
                f"latest Salary Structure Assignment from date {ssa_date_str}."
            )

        if not self.components:
            frappe.throw("No components found to calculate new Salary Structure Assignment")

        comp_row = self.components[0]

        ssa_doc = frappe.get_doc({
            "doctype": "Salary Structure Assignment",
            "employee": self.employee,
            "custom_salary_increment": self.name,
            "salary_structure": latest_ssa.salary_structure,
            "from_date": inc_row.increment_date,
        })

        for f in self.component_fields:
            base_val = getattr(comp_row, f, 0) or 0
            inc_val = getattr(inc_row, f, 0) or 0
            ssa_doc.set(f, base_val + inc_val)

        ssa_doc.insert(ignore_permissions=True)
        ssa_doc.submit()

        frappe.msgprint(f"New Salary Structure Assignment created successfully.", alert=True)



@frappe.whitelist()
def create_increment(docname, data):
    if isinstance(data, str):
        data = json.loads(data)

    doc = frappe.get_doc("Salary Increment", docname)

    component_fields = [
        "sc_basic","sc_hra","sc_transport","sc_other","sc_mobile",
        "sc_car","custom_leave_encashment_amount_per_day","sc_cola",
        "holiday_ot_rate","ot_rate","sc_fuel"
    ]

    exclude_fields = ["custom_pension_percentage", "leave_salary"]

    latest_ssa = frappe.get_all(
        "Salary Structure Assignment",
        filters={"employee": doc.employee, "docstatus": 1},
        fields=component_fields + exclude_fields,
        order_by="from_date desc",
        limit_page_length=1
    )
    
    latest_values = {f: 0 for f in component_fields + exclude_fields}
    if latest_ssa:
        latest_ssa = latest_ssa[0]
        for f in latest_values:
            latest_values[f] = latest_ssa.get(f) or 0

    row = doc.append("increments", {})

    for f in component_fields + exclude_fields:
        row.set(f, data.get(f) or 0)

    row.increment_date = data.get("date")

    row.increment_amount = sum((data.get(f, 0) or 0) for f in component_fields)

    latest_total = sum(latest_values[f] for f in component_fields)
    row.net_amount = latest_total + row.increment_amount

    ssa_data = {
        "doctype": "Salary Structure Assignment",
        "employee": doc.employee,
        "custom_salary_increment": doc.name,
        "salary_structure": data.get("salary_structure"),
        "from_date": data.get("date")
    }

    for f in component_fields:
        old_val = latest_values.get(f, 0) or 0
        new_inc = data.get(f) or 0
        ssa_data[f] = old_val + new_inc if new_inc > 0 else old_val

    for f in exclude_fields:
        old_val = latest_values.get(f, 0) or 0
        new_val = data.get(f) or 0
        
        ssa_data[f] = old_val + new_val if new_val != old_val else old_val

    ssa = frappe.get_doc(ssa_data)
    ssa.insert(ignore_permissions=True)
    ssa.submit()

    doc.save(ignore_permissions=True)
    return {"status": "success", "ssa": ssa.name}



@frappe.whitelist()
def get_latest_salary_structure(employee, increment_date=None):
    """
    Fetch latest Salary Structure Assignment for an employee.
    Optionally validate an increment date against the latest SSA from_date.
    Returns SSA details and raises exception if increment_date is earlier than latest SSA.
    """
    ssa = frappe.db.get_all(
        "Salary Structure Assignment",
        filters={"employee": employee, "docstatus": 1},
        fields=[
            "name",
            "from_date",
            "salary_structure",
            "sc_basic", "sc_hra", "sc_transport", "sc_other",
            "sc_mobile", "sc_car",
            "custom_leave_encashment_amount_per_day",
            "sc_cola", "holiday_ot_rate", "ot_rate", "sc_fuel",
            "custom_pension_percentage","leave_salary"
        ],
        order_by="from_date desc",
        limit_page_length=1
    )

    if not ssa:
        return None

    latest_ssa = ssa[0]

    if increment_date:
        from frappe.utils import getdate
        increment_date = getdate(increment_date)
        if increment_date < latest_ssa.from_date:
            frappe.throw(f"Increment date cannot be earlier than latest Salary Structure Assignment.")

    return latest_ssa