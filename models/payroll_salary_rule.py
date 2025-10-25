# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_globals = {'__builtins__': None}

            try:
                exec(self.amount_python_compute or '', safe_globals, localdict)
            except Exception as e:
                raise UserError(f'Lỗi khi thực thi quy tắc {self.name} ({self.code}): {e}')

            return float(localdict.get('result', 0.0))


# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()
        
        # Nếu quy tắc bị tắt, không tính
        if not self.is_active:
            return 0.0
        
        if self.amount_type == 'fixed':
            return self.amount_fixed
            
        elif self.amount_type == 'percentage':
            base_amount = rules.get(self.amount_percentage_base, 0.0)
            return base_amount * self.amount_percentage / 100.0
            
        elif self.amount_type == 'code':
            localdict = {
                'contract': contract,
                'employee': employee,
                'payslip': payslip,
                'rules': rules,
                'result': 0.0,
            }
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return localdict.get('result', 0.0)
            
        return 0.0

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

class PayrollSalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Quy tắc lương'
    _order = 'sequence, code'

    name = fields.Char('Tên quy tắc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=100)

    active = fields.Boolean(
        default=True,
        help="Đặt thành False để ẩn quy tắc lương mà không xóa nó."
    )

    is_active = fields.Boolean('Hoạt động', default=True,
                               help='Bật/Tắt để quy tắc được tính vào lương nhân viên')
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương', 
                                    required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True, default='other')
    
    amount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm'),
        ('code', 'Python Code'),
    ], string='Kiểu tính', required=True, default='fixed')
    
    amount_fixed = fields.Float('Số tiền cố định')
    amount_percentage = fields.Float('Phần trăm (%)')
    amount_percentage_base = fields.Char('Mã quy tắc cơ sở', 
                                         help='Mã của quy tắc để tính % (ví dụ: BASIC)')
    amount_python_compute = fields.Text('Python Code', 
        default="""# Available variables:
# - contract: employee.management.contract
# - employee: employee.management.employee  
# - payslip: payroll.payslip
# - rules: dict chứa các rule đã tính (key=code, value=amount)
# Return: result = 0.0

result = 0.0
""")
    
    note = fields.Text('Ghi chú')
    appears_on_payslip = fields.Boolean('Hiển thị trên phiếu lương', default=True)
    
    _sql_constraints = [
        ('code_structure_unique', 'unique(code, structure_id)', 
         'Mã quy tắc phải là duy nhất trong cấu trúc!')
    ]
    
    def compute_rule(self, contract, employee, payslip, rules):
        """Tính toán giá trị của rule - chỉ tính nếu is_active=True"""
        self.ensure_one()