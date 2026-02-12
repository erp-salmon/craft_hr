import frappe
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry


class CustomPayrollEntry(PayrollEntry):
	"""Custom Payroll Entry with employment_type filter"""

	def make_filters(self):
		"""Override to add employment_type filter"""
		filters = frappe._dict()
		filters["company"] = self.company
		filters["branch"] = self.branch
		filters["department"] = self.department
		filters["designation"] = self.designation
		filters["employment_type"] = self.employment_type

		return filters


def get_filter_condition(filters):
	"""Override filter condition to include employment_type"""
	cond = ""
	for f in ["company", "branch", "department", "designation", "employment_type"]:
		if filters.get(f):
			cond += " and t1." + f + " = " + frappe.db.escape(filters.get(f))

	return cond


# Monkey patch the get_filter_condition function
import hrms.payroll.doctype.payroll_entry.payroll_entry as payroll_entry_module
payroll_entry_module.get_filter_condition = get_filter_condition
