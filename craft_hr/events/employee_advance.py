


import frappe

def validate(self, method=None):
        if not hasattr(self, "_original_advance_account"):
            self._original_advance_account = self.advance_account

        if self.is_leave_salary:
            if self.company:
                leave_account = frappe.db.get_value(
                    "Company", self.company, "leave_salary_advance_account"
                )
                if leave_account:
                    self.advance_account = leave_account
                else:
                    frappe.throw(f"No Leave Salary Advance Account set in Company {self.company}")
        else:
            if hasattr(self, "_original_advance_account"):
                self.advance_account = self._original_advance_account