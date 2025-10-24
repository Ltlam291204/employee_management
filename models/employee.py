# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import random
import string

class Employee(models.Model):
    _name = 'employee.management.employee'
    _description = 'Hồ sơ Nhân viên'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name_char'

    # Trường tài khoản Odoo
    name = fields.Many2one('res.users', 
                            string='Tài khoản Odoo', 
                            ondelete='restrict', 
                            tracking=True,
                            readonly=True,
                            help="Tài khoản Odoo được tạo tự động từ email.")
    
    # Checkbox để quyết định có tạo tài khoản Odoo hay không
    create_odoo_account = fields.Boolean(
        'Tạo tài khoản Odoo',
        default=False,
        tracking=True,
        help="Tích vào ô này nếu muốn tạo tài khoản Odoo cho nhân viên này"
    )
    
    # Lưu mật khẩu hiện tại
    current_password = fields.Char(
        'Mật khẩu hiện tại',
        readonly=True,
        groups='employee_management.group_manager',
        help="Mật khẩu hiện tại của tài khoản. Chỉ Giám đốc xem được."
    )
    
    # Tên nhân viên
    display_name_char = fields.Char('Tên Nhân viên', required=True, tracking=True) 
    email = fields.Char('Email', tracking=True)
    phone = fields.Char('Số điện thoại', tracking=True)
    department = fields.Char('Phòng ban', tracking=True)
    position = fields.Char('Chức danh', tracking=True)
    
    # Trường chọn quyền
    user_role = fields.Selection([
        ('employee', 'Nhân viên'),
        ('officer', 'Cán bộ'),
        ('manager', 'Giám đốc')
    ], string='Quyền hạn', default='employee', required=True, tracking=True,
       help="Chọn quyền cho tài khoản Odoo của nhân viên này")

    # Thông tin bổ sung
    date_of_birth = fields.Date('Ngày sinh')
    identification_number = fields.Char('Số CMND/CCCD')
    address = fields.Text('Địa chỉ')
    emergency_contact = fields.Char('Tên người liên hệ khẩn cấp')
    emergency_phone = fields.Char('SĐT khẩn cấp')
    
    # Trạng thái
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('active', 'Đang làm việc'),
        ('inactive', 'Ngừng làm việc')
    ], string='Trạng thái', default='draft', tracking=True)
    
    # Quan hệ hợp đồng và lương
    contract_ids = fields.One2many('employee.management.contract', 'employee_id', string='Hợp đồng')
    current_contract_id = fields.Many2one('employee.management.contract', string='Hợp đồng hiện tại', 
                                         compute='_compute_current_contract', store=True)
    
    # THAY ĐỔI: current_salary lấy từ phiếu lương gần nhất
    current_salary = fields.Float('Lương hiện tại', compute='_compute_current_salary', store=True,
                                   help="Lương thực nhận từ phiếu lương gần nhất")
    
    payslip_ids = fields.One2many('payroll.payslip', 'employee_id', string='Phiếu lương')
    latest_payslip_id = fields.Many2one('payroll.payslip', string='Phiếu lương gần nhất',
                                        compute='_compute_latest_payslip', store=True)
    
    _sql_constraints = [
        ('identification_number_unique', 'unique(identification_number)', 'Số CMND/CCCD phải là duy nhất!'),
    ]
    
    def _generate_random_password(self, length=10):
        """Tạo mật khẩu ngẫu nhiên"""
        characters = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choice(characters) for i in range(length))
        return password
    
    @api.constrains('identification_number')
    def _check_identification_unique(self):
        for record in self:
            if record.identification_number:
                other_employee = self.search([
                    ('identification_number', '=', record.identification_number),
                    ('id', '!=', record.id)
                ])
                if other_employee:
                    raise ValidationError(
                        f"Số CMND/CCCD '{record.identification_number}' đã được sử dụng cho nhân viên '{other_employee.display_name_char}'!"
                    )
    
    @api.constrains('create_odoo_account', 'email')
    def _check_email_when_account_created(self):
        """Nếu tạo tài khoản Odoo, email là bắt buộc"""
        for record in self:
            if record.create_odoo_account and not record.email:
                raise ValidationError(
                    "Email là bắt buộc khi tạo tài khoản Odoo!"
                )
    
    @api.model
    def create(self, vals):
        # Chỉ tạo User nếu checkbox create_odoo_account được tích
        if vals.get('create_odoo_account') and vals.get('email') and not vals.get('name'):
            # Tạo login từ email
            login_name = vals['email'].split('@')[0].lower()
            employee_name = vals.get('display_name_char', 'Nhân viên mới')
            
            # Tạo mật khẩu ngẫu nhiên
            random_password = self._generate_random_password()
            vals['current_password'] = random_password
            
            # Xác định quyền
            role = vals.get('user_role', 'employee')
            if role == 'manager':
                groups = [
                    self.env.ref('base.group_user').id,
                    self.env.ref('employee_management.group_manager').id,
                    self.env.ref('employee_management.group_payroll_manager').id
                ]
            elif role == 'officer':
                groups = [
                    self.env.ref('base.group_user').id,
                    self.env.ref('employee_management.group_employee').id,
                    self.env.ref('employee_management.group_payroll_officer').id
                ]
            else:
                groups = [
                    self.env.ref('base.group_user').id,
                    self.env.ref('employee_management.group_employee').id,
                    self.env.ref('employee_management.group_payroll_employee').id
                ]
            
            # Tạo User mới
            new_user = self.env['res.users'].sudo().create({
                'name': employee_name,
                'login': login_name,
                'email': vals['email'],
                'password': random_password,
                'groups_id': [(6, 0, groups)],
            })
            
            vals['name'] = new_user.id
        
        employee = super().create(vals)
        
        # Gửi thông báo với mật khẩu
        if employee.create_odoo_account and employee.current_password:
            employee.message_post(
                body=f"""
                <div style='background-color: #e8f5e9; padding: 15px; border-radius: 5px; border-left: 4px solid #4caf50;'>
                    <h3 style='color: #2e7d32; margin-top: 0;'>🔑 Tài khoản Odoo đã được tạo</h3>
                    <p><strong>Tên đăng nhập:</strong> {employee.name.login}</p>
                    <p><strong>Email:</strong> {employee.email}</p>
                    <p><strong>Mật khẩu:</strong> <code style='background: #fff; padding: 4px 8px; border-radius: 3px; font-size: 14px;'>{employee.current_password}</code></p>
                    <p style='color: #d32f2f; margin-bottom: 0;'><em>⚠️ Vui lòng lưu lại mật khẩu này!</em></p>
                </div>
                """,
                subject="Thông tin tài khoản mới"
            )
        
        return employee

    def write(self, vals):
        # Khi thay đổi create_odoo_account từ False thành True
        if 'create_odoo_account' in vals and vals['create_odoo_account'] and not self.name:
            if not self.email:
                raise ValidationError("Email là bắt buộc khi tạo tài khoản Odoo!")
            
            for record in self:
                # Tạo login từ email
                login_name = record.email.split('@')[0].lower()
                employee_name = record.display_name_char or 'Nhân viên'
                
                # Tạo mật khẩu ngẫu nhiên
                random_password = self._generate_random_password()
                vals['current_password'] = random_password
                
                # Xác định quyền
                role = vals.get('user_role', record.user_role)
                if role == 'manager':
                    groups = [
                        self.env.ref('base.group_user').id,
                        self.env.ref('employee_management.group_manager').id,
                        self.env.ref('employee_management.group_payroll_manager').id
                    ]
                elif role == 'officer':
                    groups = [
                        self.env.ref('base.group_user').id,
                        self.env.ref('employee_management.group_employee').id,
                        self.env.ref('employee_management.group_payroll_officer').id
                    ]
                else:
                    groups = [
                        self.env.ref('base.group_user').id,
                        self.env.ref('employee_management.group_employee').id,
                        self.env.ref('employee_management.group_payroll_employee').id
                    ]
                
                # Tạo User mới
                new_user = self.env['res.users'].sudo().create({
                    'name': employee_name,
                    'login': login_name,
                    'email': record.email,
                    'password': random_password,
                    'groups_id': [(6, 0, groups)],
                })
                
                vals['name'] = new_user.id
                
                # Gửi thông báo
                record.message_post(
                    body=f"""
                    <div style='background-color: #e8f5e9; padding: 15px; border-radius: 5px; border-left: 4px solid #4caf50;'>
                        <h3 style='color: #2e7d32; margin-top: 0;'>🔑 Tài khoản Odoo đã được tạo</h3>
                        <p><strong>Tên đăng nhập:</strong> {new_user.login}</p>
                        <p><strong>Email:</strong> {record.email}</p>
                        <p><strong>Mật khẩu:</strong> <code style='background: #fff; padding: 4px 8px; border-radius: 3px; font-size: 14px;'>{random_password}</code></p>
                        <p style='color: #d32f2f; margin-bottom: 0;'><em>⚠️ Vui lòng lưu lại mật khẩu này!</em></p>
                    </div>
                    """,
                    subject="Thông tin tài khoản mới"
                )
        
        # Khi thay đổi quyền, cập nhật groups của User
        if 'user_role' in vals and self.name:
            for record in self:
                if record.name:
                    if vals['user_role'] == 'manager':
                        groups = [
                            self.env.ref('base.group_user').id,
                            self.env.ref('employee_management.group_manager').id,
                            self.env.ref('employee_management.group_payroll_manager').id
                        ]
                    elif vals['user_role'] == 'officer':
                        groups = [
                            self.env.ref('base.group_user').id,
                            self.env.ref('employee_management.group_employee').id,
                            self.env.ref('employee_management.group_payroll_officer').id
                        ]
                    else:
                        groups = [
                            self.env.ref('base.group_user').id,
                            self.env.ref('employee_management.group_employee').id,
                            self.env.ref('employee_management.group_payroll_employee').id
                        ]
                    
                    record.name.sudo().write({
                        'groups_id': [(6, 0, groups)]
                    })
        
        # Khi thay đổi tên hoặc email, cập nhật User
        if ('display_name_char' in vals or 'email' in vals) and self.name:
            for record in self:
                user_vals = {}
                if 'display_name_char' in vals:
                    user_vals['name'] = vals['display_name_char']
                if 'email' in vals:
                    user_vals['email'] = vals['email']
                
                if user_vals:
                    record.name.sudo().write(user_vals)
        
        return super().write(vals)

    @api.depends('contract_ids.state', 'contract_ids.date_start', 'contract_ids.date_end')
    def _compute_current_contract(self):
        for employee in self:
            current_contract = employee.contract_ids.filtered(
                lambda c: c.state == 'open' and 
                          c.date_start <= fields.Date.today() and
                          (not c.date_end or c.date_end >= fields.Date.today())
            )
            employee.current_contract_id = current_contract[:1] if current_contract else False
    
    @api.depends('payslip_ids.state', 'payslip_ids.date_to')
    def _compute_latest_payslip(self):
        """Tìm phiếu lương gần nhất đã hoàn thành"""
        for employee in self:
            latest = employee.payslip_ids.filtered(
                lambda p: p.state == 'done'
            ).sorted('date_to', reverse=True)
            employee.latest_payslip_id = latest[:1] if latest else False
    
    @api.depends('latest_payslip_id.net_wage')
    def _compute_current_salary(self):
        """Lương hiện tại = Lương thực nhận từ phiếu lương gần nhất"""
        for employee in self:
            employee.current_salary = employee.latest_payslip_id.net_wage if employee.latest_payslip_id else 0.0

    def action_activate(self):
        self.write({'state': 'active'})
    
    def action_deactivate(self):
        self.write({'state': 'inactive'})
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.display_name_char}"
            result.append((record.id, name))
        return result
    
    def action_reset_password(self):
        """Đổi mật khẩu cho nhân viên"""
        self.ensure_one()
        if not self.name:
            raise UserError("Nhân viên này chưa có tài khoản liên kết!")
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Đổi Mật khẩu',
            'res_model': 'employee.reset.password.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_id': self.id,
                'default_user_id': self.name.id,
                'default_current_password_display': self.current_password,
            }
        }


class EmployeeResetPasswordWizard(models.TransientModel):
    _name = 'employee.reset.password.wizard'
    _description = 'Wizard Đổi Mật khẩu'

    employee_id = fields.Many2one('employee.management.employee', string='Nhân viên', required=True, readonly=True)
    user_id = fields.Many2one('res.users', string='Tài khoản', required=True, readonly=True)
    
    # Hiển thị mật khẩu hiện tại
    current_password_display = fields.Char(
        'Mật khẩu hiện tại', 
        readonly=True,
        help="Mật khẩu đang được sử dụng"
    )
    
    new_password = fields.Char('Mật khẩu mới', required=True)
    confirm_password = fields.Char('Xác nhận mật khẩu mới', required=True)

    @api.constrains('new_password', 'confirm_password')
    def _check_password_match(self):
        for wizard in self:
            if wizard.new_password != wizard.confirm_password:
                raise ValidationError("Mật khẩu xác nhận không khớp!")

    def action_confirm_reset(self):
        self.ensure_one()
        
        if self.new_password != self.confirm_password:
            raise UserError("Mật khẩu xác nhận không khớp!")
        
        # Đổi mật khẩu
        self.user_id.sudo().write({
            'password': self.new_password
        })
        
        # Cập nhật mật khẩu hiện tại vào employee
        self.employee_id.sudo().write({
            'current_password': self.new_password
        })
        
        # Gửi thông báo vào chatter
        self.employee_id.message_post(
            body=f"""
            <div style='background-color: #fff3e0; padding: 15px; border-radius: 5px; border-left: 4px solid #ff9800;'>
                <h3 style='color: #e65100; margin-top: 0;'>🔄 Mật khẩu đã được thay đổi</h3>
                <p><strong>Tài khoản:</strong> {self.user_id.login}</p>
                <p><strong>Email:</strong> {self.user_id.email}</p>
                <p><strong>Mật khẩu mới:</strong> <code style='background: #fff; padding: 4px 8px; border-radius: 3px; font-size: 14px;'>{self.new_password}</code></p>
                <p style='color: #d32f2f; margin-bottom: 0;'><em>⚠️ Vui lòng thông báo cho nhân viên!</em></p>
            </div>
            """,
            subject="Mật khẩu đã được thay đổi"
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Thành công!',
                'message': f'Đã đổi mật khẩu cho {self.employee_id.display_name_char}. Mật khẩu mới: {self.new_password}',
                'type': 'success',
                'sticky': True,
            }
        }