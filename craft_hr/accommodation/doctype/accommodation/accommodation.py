# Copyright (c) 2025, Craftinteractive and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Accommodation(Document):
	pass


@frappe.whitelist()
def update_counts(accommodation_name, save_doc = False):
	acc_doc = frappe.get_doc("Accommodation", accommodation_name)

	if not acc_doc.building_name:
		return {
			"floor": 0,
			"room": 0,
			"bed": 0,
			"building_name": acc_doc.building_name
		}

	beds = frappe.get_all(
		"Bed", 
		filters={"building_name": acc_doc.building_name},
		fields=["floor_no", "room_no","name"]
	)

	# Use sets to count unique floors and rooms
	unique_floors = set()
	unique_rooms = set()

	for bed in beds:
		unique_floors.add(bed["floor_no"])
		unique_rooms.add(bed["room_no"])

	# Update the Accommodation document with the new counts
	acc_doc.floor = len(unique_floors)
	acc_doc.room = len(unique_rooms)
	acc_doc.bed = len(beds) 

	if save_doc:
		acc_doc.save()

	return {
		"floor": acc_doc.floor,
		"room": acc_doc.room,
		"bed": acc_doc.bed,
		"building_name": acc_doc.building_name
	}
