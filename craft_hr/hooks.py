from . import __version__ as app_version

app_name = "craft_hr"
app_title = "Craft HR"
app_publisher = "Craftinteractive"
app_description = "HR Management System adhering to UAE Labour Law"
app_email = "info@craftinteractive.ae"
app_license = "MIT"

fixtures = [
    {'dt':'Custom Field', 'filters':[['module', 'in', {"Craft HR", "OT Mgmt","Accommodation"}]]},
    {'dt':'Property Setter', 'filters':[['module', 'in', {"Craft HR", "OT Mgmt", "Accommodation"}]]},
    {'dt':'Report', 'filters':[['name', 'in', {"Overtime Summary", "Accommodation"}]]},
    {'dt':'Module Def', 'filters':[['name', 'in', {"Accommodation"}]]},
    {'dt':'Workspace', 'filters':[['name', 'in', {"Accommodation"}]]},

    ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/craft_hr/css/craft_hr.css"
# app_include_js = "/assets/craft_hr/js/craft_hr.js"

# include js, css files in header of web template
# web_include_css = "/assets/craft_hr/css/craft_hr.css"
# web_include_js = "/assets/craft_hr/js/craft_hr.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "craft_hr/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}

doctype_js = {
    "Leave Allocation":"public/js/leave_allocation.js",
    "Additional Salary":"public/js/additional_salary.js",
    "Shift Type":"public/js/shift_type.js",
    "Payroll Entry":"public/js/payroll_entry.js",
    "Company":"public/js/company.js",
    "Employee Advance":"public/js/employee_advance.js",
}

# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "craft_hr.utils.jinja_methods",
#	"filters": "craft_hr.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "craft_hr.install.before_install"
after_install = "craft_hr.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "craft_hr.uninstall.before_uninstall"
# after_uninstall = "craft_hr.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "craft_hr.utils.before_app_install"
# after_app_install = "craft_hr.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "craft_hr.utils.before_app_uninstall"
# after_app_uninstall = "craft_hr.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "craft_hr.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	# "ToDo": "custom_app.overrides.CustomToDo"
	"Leave Encashment":"craft_hr.overrides.leave_encashment.CustomLeaveEncashment",



 
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

doc_events = {
    "Leave Allocation":{
        "validate": "craft_hr.events.leave_allocation.validate",
        "before_submit": "craft_hr.events.leave_allocation.before_submit",
        # "after_submit": "craft_hr.events.leave_allocation.after_submit",
    },
    "Leave Application":{
        "on_submit": [
            "craft_hr.events.leave_application.on_submit",
            "craft_hr.events.leave_application.create_deferred_leave_additional_salary"
        ],
        "validate": "craft_hr.events.leave_application.validate",
        "on_cancel": "craft_hr.events.leave_application.cancel_linked_additional_salary",
        "on_trash": "craft_hr.events.leave_application.delete_deferred_leave_additional_salary"
    },
    "Attendance":{
        "on_submit": "craft_hr.events.attendance.on_submit",
        "on_cancel": "craft_hr.events.attendance.on_cancel"
    },
	"Salary Slip": {
		"before_validate": "craft_hr.events.salary_slip.before_validate"
	},
    "Shift Type": {
        "before_validate":"craft_hr.events.shift_type.before_validate"
	},
    "Salary Structure Assignment": {
        "validate":"craft_hr.events.salary_structure_assignment.validate"
	},
    "Additional Salary": {
        "before_submit": "craft_hr.events.additional_salary.mark_deductions_as_reimbursed",
        "on_cancel": "craft_hr.events.additional_salary.unmark_deductions_as_reimbursed"

    },
    "Employee Advance": {
        "validate": "craft_hr.events.employee_advance.validate"
    },
    "Employee": {
        "on_update": "craft_hr.events.employee.on_update"
    }
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	# 	"craft_hr.tasks.all"
	# ],
	"daily": [
		"craft_hr.tasks.daily.reset_leave_allocation",
		"craft_hr.tasks.daily.update_leave_allocations",
		"craft_hr.tasks.daily.close_expired_allocations",
		"craft_hr.craft_hr.doctype.ticket_allocation.ticket_allocation.daily_event",
	],
	# "hourly": [
	# 	"craft_hr.tasks.hourly"
	# ],
	# "weekly": [
	# 	"craft_hr.tasks.weekly.update_leave_allocations"
	# ],
	# "monthly": [
	# 	"craft_hr.tasks.monthly"
	# ],
}

# Testing
# -------

# before_tests = "craft_hr.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "craft_hr.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "craft_hr.task.get_dashboard_data"
# }

override_doctype_dashboards = {
    "Employee": "craft_hr.overrides.dashboard_overrides.get_dashboard_for_employee",

}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["craft_hr.utils.before_request"]
# after_request = ["craft_hr.utils.after_request"]

# Job Events
# ----------
# before_job = ["craft_hr.utils.before_job"]
# after_job = ["craft_hr.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"craft_hr.auth.validate"
# ]

#TODO: Not Working. 2 overrides...
override_doctype_dashboards = {
	"Employee": "craft_hr.overrides.dashboard_overrides.get_dashboard_for_employee",
}
