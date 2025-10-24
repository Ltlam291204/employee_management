# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date, timedelta
from odoo.exceptions import UserError, ValidationError

class EmployeeContract(models.Model):
    _name = 'employee.management.contract'
    _description = 'Hợp đồng Lao động'
    _inherit = ['mail.thread']
    _rec_name = 'name'
    _order = 'date_start desc'

    name = fields.Char('Tham chiếu Hợp đồng', compute='_compute_contract_name', store=True, tracking=True)

    # Thông tin nhân viên
    employee_id = fields.Many2one('employee.management.employee', string='Người lao động',
                                required=True, tracking=True, ondelete='cascade')
    department = fields.Char('Phòng ban', related='employee_id.department', readonly=True)
    position = fields.Char('Chức vụ', related='employee_id.position', readonly=True)




    # THÊM PHƯƠNG THỨC NÀY
    def action_update_contract_names(self):
        """Cập nhật lại trường 'name' cho tất cả hợp đồng dựa trên tên nhân viên mới."""
        for contract in self:
            if contract.employee_id:
                # Tạo tên hợp đồng mới: "Hợp đồng của [Tên Nhân viên]"
                new_name = "Hợp đồng của %s" % (contract.employee_id.display_name_char or contract.employee_id.name.name or 'Chưa rõ')
                contract.name = new_name
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Cập nhật thành công',
                'message': f'Đã cập nhật tên tham chiếu cho {len(self)} hợp đồng.',
                'type': 'success',
                'sticky': False,
            }
        }




    # Thêm fields còn thiếu từ view
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    working_hours = fields.Float('Giờ làm việc', default=8.0)
    color = fields.Integer('Color Index', default=0)

    # Thông tin hủy hợp đồng
    cancel_date = fields.Date('Ngày hủy')
    cancel_reason = fields.Text('Lý do hủy')

    # Chi tiết hợp đồng
    date_start = fields.Date('Ngày bắt đầu', required=True, tracking=True, default=fields.Date.today)
    date_end = fields.Date('Ngày kết thúc', tracking=True)
    trial_date_end = fields.Date('Ngày kết thúc thử việc', tracking=True)

    # Thông tin lương
    base_wage = fields.Float('Lương cơ bản', required=True)
    benefit_ids = fields.One2many('employee.management.contract.benefit', 'contract_id', string='Phúc lợi')
    contribution_ids = fields.One2many('employee.management.contract.contribution', 'contract_id', string='Các khoản đóng góp')
    salary_mode = fields.Selection([
        ('staff', 'Lương nhân viên'),
        ('hr', 'Lương HR'),
        ('director', 'Lương giám đốc'),
    ], string='Chế độ lương', required=True)

    # Tính toán lương
    total_benefit = fields.Float('Tổng phúc lợi', compute='_compute_total_benefit', store=True)
    total_contribution = fields.Float('Tổng đóng góp', compute='_compute_total_contribution', store=True)
    total_salary = fields.Float('Tổng lương', compute='_compute_total_salary', store=True)

    # Trạng thái
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('open', 'Đang làm việc'),
        ('expired', 'Hết hạn'),
        ('cancel', 'Đã hủy')
    ], string='Trạng thái', default='draft', tracking=True)

    # Currency field cho monetary widget
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                 default=lambda self: self.env.company.currency_id)

    # Thêm field để theo dõi việc cảnh báo hết hạn
    expiry_warning_sent = fields.Boolean('Đã gửi cảnh báo hết hạn', default=False)
    working_hour_template_id = fields.Many2one(
        'employee.management.working.hour.template',
        string='Mẫu giờ làm việc',
        required=False
    )

    tax_policy = fields.Selection([
        ('none', 'Không áp dụng'),
        ('tncn_bac_thue', 'TNCN theo bậc thuế'),
        ('khac', 'Khác')
    ], string='Chính sách thuế TNCN', required=True, default='none')

    @api.depends('benefit_ids.amount')
    def _compute_total_benefit(self):
        for contract in self:
            contract.total_benefit = sum(contract.benefit_ids.mapped('amount'))

    @api.depends('contribution_ids')
    def _compute_total_contribution(self):
        """Tổng đóng góp = Số lượng kiểu đóng góp (không có số tiền)"""
        for contract in self:
            contract.total_contribution = len(contract.contribution_ids)

    @api.depends('base_wage', 'total_benefit', 'total_contribution')
    def _compute_total_salary(self):
        for contract in self:
            # Không trừ contribution vì không có số tiền
            contract.total_salary = contract.base_wage + contract.total_benefit

    @api.model
    def create(self, vals):
        # 1. Tự động tạo tên (name) nếu chưa được cung cấp
        if 'name' not in vals or not vals.get('name'):
            employee = False
            # Nếu có employee_id, tìm thông tin nhân viên
            if vals.get('employee_id'):
                # Sử dụng self.env.ref.env.context(lang='vi_VN') để lấy tên nhân viên có dấu tiếng Việt nếu cần.
                # Tuy nhiên, chỉ cần browse là đủ vì display_name_char đã có sẵn.
                employee = self.env['employee.management.employee'].browse(vals['employee_id'])

            if employee and employee.exists():
                # Sử dụng display_name_char (là tên char của nhân viên)
                employee_name = employee.display_name_char or employee.name.name or 'Chưa rõ tên'
                
                # Đếm số hợp đồng hiện có của nhân viên ĐANG HOẠT ĐỘNG (ngoại trừ trạng thái 'cancel' và 'expired' nếu có)
                # Giả sử trạng thái đang hoạt động là 'draft', 'open', 'pending'
                # CÁCH CẢI TIẾN: Chỉ đếm các hợp đồng KHÔNG phải là draft/expired/cancel để số lần là chính xác hơn cho hợp đồng mới.
                contract_count = self.search_count([
                    ('employee_id', '=', vals['employee_id']),
                    ('state', 'not in', ['draft', 'cancel', 'expired', 'close']) 
                ])
                contract_number = contract_count + 1
                
                # Tạo tên hợp đồng theo format mới (Có sử dụng f-string, tương tự code gốc)
                vals['name'] = f"Hợp đồng của {employee_name} lần {contract_number}"
            else:
                # Nếu không có employee_id hoặc không tìm thấy, sử dụng sequence
                vals['name'] = self.env['ir.sequence'].next_by_code('employee.management.contract') or 'CONTRACT001'
                
        # 2. Xử lý logic khác (nếu có) trước khi gọi super().create(vals)

        return super().create(vals)
    def write(self, vals):
        # Đảm bảo logic này hoạt động trên tất cả các bản ghi đang được ghi
        if 'date_end' in vals:
            # Khi ngày kết thúc bị thay đổi, reset cờ cảnh báo hết hạn
            vals['expiry_warning_sent'] = False
            
        # CẢI TIẾN: Nếu employee_id thay đổi, ta nên cập nhật lại tên hợp đồng
        if 'employee_id' in vals and self.employee_id.id != vals['employee_id']:
            employee = self.env['employee.management.employee'].browse(vals['employee_id'])
            if employee and employee.exists():
                employee_name = employee.display_name_char or employee.name.name or 'Chưa rõ tên'
                
                contract_count = self.search_count([
                    ('employee_id', '=', vals['employee_id']),
                    ('state', 'not in', ['draft', 'cancel', 'expired', 'close']),
                    ('id', '!=', self.id) # Loại bỏ chính bản ghi đang được ghi (đang được update)
                ])
                contract_number = contract_count + 1
                vals['name'] = f"Hợp đồng của {employee_name} lần {contract_number}"


        return super().write(vals)


    def action_start_contract(self):
        for contract in self:
            if contract.state == 'draft':
                contract.state = 'open'
                # Sử dụng _() để hỗ trợ dịch thuật trong Odoo
                contract.message_post(body=_("Hợp đồng đã được khởi động và chuyển sang trạng thái 'Đang làm việc'."))
        return True

    def action_renew_contract(self):
        self.ensure_one()
        return {
            'name': 'Gia hạn Hợp đồng',
            'type': 'ir.actions.act_window',
            'res_model': 'employee.contract.renew.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
                'default_current_end_date': self.date_end,
                'default_new_end_date': self.date_end + timedelta(days=365) if self.date_end else fields.Date.today() + timedelta(days=365)
            }
        }

    def action_close_contract(self):
        for contract in self:
            contract.state = 'close'

    def action_cancel_contract(self):
        for contract in self:
            if contract.state not in ['close', 'cancel']:
                return {
                    'name': 'Hủy Hợp đồng',
                    'type': 'ir.actions.act_window',
                    'res_model': 'employee.contract.cancel.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {'default_contract_id': contract.id}
                }
        return True

    def action_set_draft(self):
        for contract in self:
            contract.state = 'draft'

    @api.model
    def _cron_check_contract_expiry(self):
        today = fields.Date.today()
        
        expired_contracts = self.search([
            ('state', '=', 'open'),
            ('date_end', '!=', False),
            ('date_end', '<', today)
        ])
        
        if expired_contracts:
            expired_contracts.write({'state': 'expired'})
            
            for contract in expired_contracts:
                contract.message_post(
                    body=f"🚨 <b>Hợp đồng đã hết hạn!</b><br/>"
                         f"Hợp đồng đã tự động chuyển sang trạng thái 'Hết hạn' vào ngày {today.strftime('%d/%m/%Y')}.<br/>"
                         f"Vui lòng liên hệ bộ phận HR để gia hạn hoặc xử lý."
                )
        
        warning_date = today + timedelta(days=7)
        soon_expired_contracts = self.search([
            ('state', '=', 'open'),
            ('date_end', '!=', False),
            ('date_end', '<=', warning_date),
            ('date_end', '>=', today),
            ('expiry_warning_sent', '=', False)
        ])
        
        if soon_expired_contracts:
            for contract in soon_expired_contracts:
                days_left = (contract.date_end - today).days
                contract.message_post(
                    body=f"🚨 <b>Cảnh báo hợp đồng sắp hết hạn!</b><br/>"
                         f"Hợp đồng sẽ hết hạn vào ngày {contract.date_end.strftime('%d/%m/%Y')} "
                         f"(còn {days_left} ngày).<br/>"
                         f"Vui lòng chuẩn bị gia hạn hoặc xử lý kịp thời."
                )
                contract.expiry_warning_sent = True
        
        return True

    @api.onchange('date_end')
    def _onchange_date_end(self):
        today = fields.Date.context_today(self)
        for contract in self:
            if contract.date_end:
                if contract.date_end < today:
                    contract.state = 'expired'
                else:
                    contract.state = 'open'


class ContractBenefit(models.Model):
    _name = 'employee.management.contract.benefit'
    _description = 'Phúc lợi Hợp đồng'

    contract_id = fields.Many2one('employee.management.contract', string='Hợp đồng', ondelete='cascade')
    name = fields.Char('Loại phúc lợi', required=True)
    benefit_type = fields.Selection([
        ('allowance', 'Phụ cấp'),
        ('bonus', 'Thưởng'),
        ('insurance', 'Bảo hiểm'),
        ('other', 'Khác')
    ], string='Loại', default='allowance')
    amount = fields.Float('Số tiền', required=True)
    currency_id = fields.Many2one('res.currency', related='contract_id.currency_id', store=True)


class ContractContribution(models.Model):
    _name = 'employee.management.contract.contribution'
    _description = 'Đóng góp hợp đồng'

    contract_id = fields.Many2one('employee.management.contract', string='Hợp đồng', ondelete='cascade')
    contribution_type_id = fields.Many2one(
        'employee.management.contribution.type', 
        string='Kiểu đóng góp', 
        required=True
    )
    name = fields.Char(string='Tên', related='contribution_type_id.name', store=True, readonly=True)


class ContributionType(models.Model):
    """Model để quản lý các kiểu đóng góp"""
    _name = 'employee.management.contribution.type'
    _description = 'Kiểu Đóng góp'
    _order = 'sequence, name'

    name = fields.Char('Tên kiểu đóng góp', required=True)
    code = fields.Char('Mã', required=True)
    description = fields.Text('Mô tả')
    sequence = fields.Integer('Thứ tự', default=10)
    active = fields.Boolean('Hoạt động', default=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã kiểu đóng góp phải là duy nhất!')
    ]


class WorkingHourTemplate(models.Model):
    _name = 'employee.management.working.hour.template'
    _description = 'Mẫu giờ làm việc'

    name = fields.Char('Tên mẫu', required=True)
    hours_per_week = fields.Float('Số giờ/tuần', required=True)


class TaxPolicy(models.Model):
    _name = 'employee.management.tax.policy'
    _description = 'Chính sách thuế'

    name = fields.Char('Tên chính sách', required=True)
    description = fields.Text('Mô tả')
    rule_ids = fields.One2many('employee.management.tax.policy.rule', 'tax_policy_id', string='Quy tắc bậc thuế')


class TaxPolicyRule(models.Model):
    _name = 'employee.management.tax.policy.rule'
    _description = 'Quy tắc bậc thuế'

    tax_policy_id = fields.Many2one('employee.management.tax.policy', string='Chính sách thuế', required=True, ondelete='cascade')
    min_income = fields.Float('Thu nhập tối thiểu', required=True)
    max_income = fields.Float('Thu nhập tối đa')
    tax_rate = fields.Float('Thuế suất (%)', required=True)


class EmployeeContractCancelWizard(models.TransientModel):
    _name = 'employee.contract.cancel.wizard'
    _description = 'Wizard Hủy hợp đồng'

    contract_id = fields.Many2one('employee.management.contract', string='Hợp đồng', required=True)
    reason = fields.Char('Lý do hủy hợp đồng', required=True)

    def action_confirm_cancel(self):
        self.ensure_one()
        if self.contract_id:
            self.contract_id.state = 'cancel'
            self.contract_id.cancel_reason = self.reason
            self.contract_id.cancel_date = fields.Date.context_today(self)
        return {'type': 'ir.actions.act_window_close'}


class EmployeeContractRenewWizard(models.TransientModel):
    _name = 'employee.contract.renew.wizard'
    _description = 'Wizard Gia hạn hợp đồng'

    contract_id = fields.Many2one('employee.management.contract', string='Hợp đồng', required=True)
    current_end_date = fields.Date('Ngày kết thúc hiện tại', related='contract_id.date_end', readonly=True)
    new_end_date = fields.Date('Ngày kết thúc mới', required=True)
    reason = fields.Char('Lý do gia hạn hợp đồng')

    def action_confirm_renew(self):
        self.ensure_one()
        if self.contract_id and self.new_end_date:
            self.contract_id.date_end = self.new_end_date
            self.contract_id.state = 'open'
            self.contract_id.expiry_warning_sent = False  # Reset cờ cảnh báo
            
            # Ghi log vào chatter
            self.contract_id.message_post(
                body=f"Hợp đồng đã được gia hạn đến {self.new_end_date.strftime('%d/%m/%Y')}<br/>"
                     f"Lý do: {self.reason or 'Không có'}"
            )
        return {'type': 'ir.actions.act_window_close'}