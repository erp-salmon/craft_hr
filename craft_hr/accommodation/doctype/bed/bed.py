# Copyright (c) 2025, Craftinteractive and contributors
# For license information, please see license.txt

# Copyright (c) 2024, Craft Interactive and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from craft_hr.accommodation.doctype.accommodation.accommodation import update_counts


class Bed(Document):
	def validate(self, method=None):
		if self.employee:
			self.status = "Allocated"
			employee_doc = frappe.get_doc("Employee", self.employee)
			employee_doc.custom_bed_number = self.name
			employee_doc.custom_room_number = self.room_no
			employee_doc.custom_floor_number = self.floor_no
			employee_doc.custom_building_name = self.building_name
			employee_doc.save()
			# frappe.msgprint(f"Updated Bed Number in Employee: {employee_doc.name}")
		# else:
		# 	self.status = "Vacant"

	def after_insert(self):
		if self.building_name:
			accommodation_docs = frappe.get_all(
				"Accommodation",
				filters={"building_name": self.building_name},
				fields=["name"]
			)

			if accommodation_docs:
				update_counts(accommodation_docs[0].name, save_doc=True)
