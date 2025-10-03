import frappe
from frappe import _, bold, msgprint
from frappe.utils import flt, cint, getdate, now, date_diff, today, formatdate, nowtime, format_datetime


@frappe.whitelist()
def get_sif_details(employee=None,pe=None,company=None):
	sl = frappe.db.get_list("Salary Slip",{'payroll_entry':pe,'docstatus':1},['employee','start_date','end_date','rounded_total'])
	data = []
	if sl:
		total = 0
		uniqueid_err = []
		agentid_err = []
		bankacc_err = []
		comp_err = []
		validation_messages = []
		for rec in sl:
			emp_doc = frappe.get_doc("Employee",rec.employee)
			if not emp_doc.unique_id:
				err = _("{0} {1}").format(rec.employee,emp_doc.employee_name)
				uniqueid_err.append(err)
			if not emp_doc.agent_id:
				err = _("{0} {1}").format(rec.employee,emp_doc.employee_name)
				agentid_err.append(err)
			if not emp_doc.bank_ac_no:
				err = _("{0} {1}").format(rec.employee,emp_doc.employee_name)
				bankacc_err.append(err)
			row = ['EDR',emp_doc.unique_id,emp_doc.agent_id,emp_doc.bank_ac_no,rec.start_date,rec.end_date,date_diff(rec.end_date,rec.start_date)+1,"{:.2f}".format(rec.rounded_total),"{:.2f}".format(0),0]
			total += rec.rounded_total
			data.append(row)

		company = frappe.get_doc("Company",company)

		if not company.bank_code:
			err = _("Employer bank code is missing for company {0}").format(frappe.bold(company))
			comp_err.append(err)

		if uniqueid_err:
			uniqueid_err.insert(0,"<b>Employee Unique Id is missing for</b> \n")

		if agentid_err:
			agentid_err.insert(0,"<b>Employee Agent Id is missing for</b> \n")

		if bankacc_err:
			bankacc_err.insert(0,"<b>Employee Bank account no is missing for</b> \n")

		validation_messages += uniqueid_err + agentid_err + bankacc_err + comp_err

		if validation_messages:
			for msg in validation_messages:
				msgprint(msg)

			raise frappe.ValidationError(validation_messages)

		data.append(['SCR',company.unique_id,company.bank_code,formatdate(getdate(today()),"YYYY-MM-dd"),format_datetime(nowtime(),"hhmm"),formatdate(sl[0].end_date,"MMYYYY"),len(sl),"{:.2f}".format(total),'AED',' '])
		filename = company.unique_id+formatdate(getdate(today()),"YYMMdd")+format_datetime(nowtime(),"hhmm")+"00"

	return data,filename