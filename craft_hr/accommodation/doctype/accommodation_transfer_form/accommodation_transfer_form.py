# Copyright (c) 2025, Craftinteractive and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document


class AccommodationTransferForm(Document):
    def validate(self):
        if self.accommodation_type == "Allocation":
            if self.to_bed_no:
                bed = frappe.get_doc("Bed",{"name" : self.to_bed_no})
                bed.floor_no = self.to_floor_no
                bed.room_no = self.to_room_no
                bed.building_name = self.to_building_name
                bed.employee = self.employee
                bed.status = "Allocated"
                bed.save()

        elif self.accommodation_type == "Transfer":
            if self.to_bed_no:
                bed = frappe.get_doc("Bed",{"name" : self.to_bed_no})
                bed.floor_no = self.to_floor_no
                bed.room_no = self.to_room_no
                bed.building_name = self.to_building_name
                bed.employee = self.employee
                bed.status = "Allocated"
                bed.save()
        
        elif self.accommodation_type == "Exit":
            if self.employee:
                employee = frappe.get_doc("Employee",{"name":self.employee})
                employee.custom_building_name = ''
                employee.custom_floor_number = ''
                employee.custom_room_number = ''
                employee.custom_bed_number = ''
                employee.save()

            if self.from_bed_no:
                bed = frappe.get_doc("Bed",{"name" : self.from_bed_no})
                bed.floor_no = ''
                bed.room_no = ''
                bed.building_name = ''
                bed.employee = ''
                bed.status = "Vacant"
                bed.save()