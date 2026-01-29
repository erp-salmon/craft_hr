# Copyright (c) 2023, Craftinteractive and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class LeaveDistributionTemplate(Document):
	def on_update(self):
		# Clear template cache when template is updated
		from craft_hr.events.get_leaves import clear_template_cache
		clear_template_cache()

	def on_trash(self):
		# Clear template cache when template is deleted
		from craft_hr.events.get_leaves import clear_template_cache
		clear_template_cache()
