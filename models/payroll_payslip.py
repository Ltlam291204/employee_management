# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class PayrollPayslip(models.Model):
    _name = 'payroll.payslip'
    _description = 'Phiếu lương'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc, id desc'

    name = fields.Char('Tham chiếu', required=True, copy=False, readonly=True, 
                       states={'draft': [('readonly', False)]}, default='New')
    
    employee_id = fields.Many2one('employee.management.employee', 'Nhân viên', 
                                   required=True, readonly=True,
                                   states={'draft': [('readonly', False)]})
    
    contract_id = fields.Many2one('employee.management.contract', 'Hợp đồng',
                                   readonly=True, states={'draft': [('readonly', False)]},
                                   domain="[('employee_id', '=', employee_id), ('state', '=', 'open')]")
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương',
                                    required=True, readonly=True,
                                    states={'draft': [('readonly', False)]})
    
    date_from = fields.Date('Từ ngày', required=True, readonly=True,
                             states={'draft': [('readonly', False)]},
                             default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date('Đến ngày', required=True, readonly=True,
                           states={'draft': [('readonly', False)]},
                           default=lambda self: fields.Date.today())
    
    date_payment = fields.Date('Ngày thanh toán', readonly=True,
                                states={'draft': [('readonly', False)]})
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('verify', 'Chờ xác nhận'),
        ('done', 'Hoàn thành'),
        ('cancel', 'Hủy')
    ], string='Trạng thái', default='draft', tracking=True)
    
    line_ids = fields.One2many(
        'payroll.payslip.line', 'payslip_id', 'Chi tiết lương',
        copy=True, readonly=True, states={'draft': [('readonly', False)]}
    )
    
    # Các trường tổng hợp
    basic_wage = fields.Monetary('Lương cơ bản', compute='_compute_totals', store=True, currency_field='currency_id')
    total_allowance = fields.Monetary('Tổng phụ cấp', compute='_compute_totals', store=True, currency_field='currency_id')
    gross_wage = fields.Monetary('Tổng thu nhập', compute='_compute_totals', store=True, currency_field='currency_id')
    total_deduction = fields.Monetary('Tổng khấu trừ', compute='_compute_totals', store=True, currency_field='currency_id')
    net_wage = fields.Monetary('Thực nhận', compute='_compute_totals', store=True, currency_field='currency_id')
    
    bhxh_amount = fields.Monetary('BHXH (8%)', compute='_compute_totals', store=True, currency_field='currency_id')
    bhyt_amount = fields.Monetary('BHYT (1.5%)', compute='_compute_totals', store=True, currency_field='currency_id')
    bhtn_amount = fields.Monetary('BHTN (1%)', compute='_compute_totals', store=True, currency_field='currency_id')
    total_insurance = fields.Monetary('Tổng bảo hiểm', compute='_compute_totals', store=True, currency_field='currency_id')
    personal_income_tax = fields.Monetary('Thuế TNCN', compute='_compute_totals', store=True, currency_field='currency_id')
    
    currency_id = fields.Many2one('res.currency', 'Tiền tệ', 
                                   default=lambda self: self.env.company.currency_id)
    
    company_id = fields.Many2one('res.company', 'Công ty', 
                                  default=lambda self: self.env.company)
    
    note = fields.Text('Ghi chú')
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('payroll.payslip') or 'New'
        return super().create(vals)
    
    @api.onchange('employee_id')
    def _onchange_employee(self):
        """Tự động lấy hợp đồng và cấu trúc lương khi chọn nhân viên"""
        if self.employee_id:
            # Tìm hợp đồng đang hoạt động
            contract = self.env['employee.management.contract'].search([
                ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'open'),
                ('date_start', '<=', self.date_to or fields.Date.today()),
                '|', ('date_end', '=', False), ('date_end', '>=', self.date_from or fields.Date.today())
            ], limit=1, order='date_start desc')
            
            if contract:
                self.contract_id = contract
            else:
                self.contract_id = False
                return {
                    'warning': {
                        'title': 'Cảnh báo',
                        'message': f'Nhân viên {self.employee_id.display_name_char} không có hợp đồng đang hoạt động!'
                    }
                }
            
            # Tự động chọn cấu trúc lương Việt Nam
            if not self.structure_id:
                structure = self.env['payroll.structure'].search([('code', '=', 'VN_SALARY')], limit=1)
                if structure:
                    self.structure_id = structure
    
    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        """Cập nhật lại contract khi thay đổi ngày"""
        if self.employee_id and self.date_from and self.date_to:
            contract = self.env['employee.management.contract'].search([
                ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'open'),
                ('date_start', '<=', self.date_to),
                '|', ('date_end', '=', False), ('date_end', '>=', self.date_from)
            ], limit=1, order='date_start desc')
            
            if contract:
                self.contract_id = contract
    
    def action_compute_sheet(self):
        """Tính toán phiếu lương - CHỈ tính các rule is_active=True"""
        for payslip in self:
            # Kiểm tra hợp đồng
            if not payslip.contract_id:
                raise UserError(
                    f'Nhân viên {payslip.employee_id.display_name_char} không có hợp đồng đang hoạt động!\n\n'
                    f'Vui lòng kiểm tra:\n'
                    f'- Hợp đồng có trạng thái "Đang làm việc"\n'
                    f'- Ngày bắt đầu <= Đến ngày của phiếu lương\n'
                    f'- Ngày kết thúc >= Từ ngày của phiếu lương (hoặc không có ngày kết thúc)'
                )
            
            if not payslip.structure_id:
                raise UserError('Vui lòng chọn cấu trúc lương!')
            
            # ========================================
            # DEBUG: Log thông tin hợp đồng
            # ========================================
            _logger.info("="*60)
            _logger.info(f"TÍNH LƯƠNG CHO: {payslip.employee_id.display_name_char}")
            _logger.info(f"Phiếu lương: {payslip.name}")
            _logger.info(f"Hợp đồng: {payslip.contract_id.name}")
            _logger.info("="*60)
            
            # Log thông tin lương cơ bản
            base_wage = payslip.contract_id.base_wage or 0
            _logger.info(f"Lương cơ bản: {base_wage:,.0f} VNĐ")
            
            # Log thông tin phúc lợi
            if payslip.contract_id.benefit_ids:
                _logger.info(f"Phúc lợi ({len(payslip.contract_id.benefit_ids)} khoản):")
                for benefit in payslip.contract_id.benefit_ids:
                    _logger.info(f"  - {benefit.name}: {benefit.amount:,.0f} VNĐ")
                total_benefits = sum(b.amount for b in payslip.contract_id.benefit_ids)
                _logger.info(f"  → Tổng phúc lợi: {total_benefits:,.0f} VNĐ")
            else:
                _logger.info("Không có phúc lợi")
            
            # Log thông tin đóng góp (QUAN TRỌNG!)
            _logger.info("-" * 60)
            if payslip.contract_id.contribution_ids:
                _logger.info(f"Ghi nhận đóng góp ({len(payslip.contract_id.contribution_ids)} loại):")
                for contrib in payslip.contract_id.contribution_ids:
                    if contrib.contribution_type_id:
                        _logger.info(f"  ✓ {contrib.contribution_type_id.code}: {contrib.contribution_type_id.name}")
                    else:
                        _logger.warning(f"  ⚠ Contribution không có type_id!")
                
                # Kiểm tra chi tiết từng loại bảo hiểm
                bhxh_check = payslip.contract_id.contribution_ids.filtered(
                    lambda c: c.contribution_type_id and c.contribution_type_id.code == 'BHXH'
                )
                bhyt_check = payslip.contract_id.contribution_ids.filtered(
                    lambda c: c.contribution_type_id and c.contribution_type_id.code == 'BHYT'
                )
                bhtn_check = payslip.contract_id.contribution_ids.filtered(
                    lambda c: c.contribution_type_id and c.contribution_type_id.code == 'BHTN'
                )
                
                _logger.info(f"Kiểm tra chi tiết:")
                _logger.info(f"  - BHXH: {'CÓ' if len(bhxh_check) > 0 else 'KHÔNG'} ({len(bhxh_check)} record)")
                _logger.info(f"  - BHYT: {'CÓ' if len(bhyt_check) > 0 else 'KHÔNG'} ({len(bhyt_check)} record)")
                _logger.info(f"  - BHTN: {'CÓ' if len(bhtn_check) > 0 else 'KHÔNG'} ({len(bhtn_check)} record)")
            else:
                _logger.warning("⚠ KHÔNG CÓ ghi nhận đóng góp nào!")
            
            _logger.info("="*60)
            
            # Xóa các dòng cũ
            payslip.line_ids.unlink()
            
            # Dictionary lưu kết quả tính toán của các rule
            rules = {}
            lines_to_create = []
            
            # Lấy tất cả rule ĐANG HOẠT ĐỘNG (is_active=True) và sắp xếp theo sequence
            active_rules = payslip.structure_id.rule_ids.filtered(lambda r: r.is_active).sorted('sequence')
            
            if not active_rules:
                raise UserError(
                    f'Cấu trúc lương "{payslip.structure_id.name}" không có quy tắc nào đang hoạt động!\n\n'
                    f'Vui lòng vào Cấu trúc lương và bật (is_active=True) các quy tắc cần thiết.'
                )
            
            _logger.info(f"Sẽ tính {len(active_rules)} quy tắc:")
            
            # Tính toán từng rule
            for rule in active_rules:
                try:
                    _logger.info(f"=> Đang tính: [{rule.code}] {rule.name}")
                    
                    amount = rule.compute_rule(
                        contract=payslip.contract_id,
                        employee=payslip.employee_id,
                        payslip=payslip,
                        rules=rules
                    )

                    # Xử lý khi amount là None
                    if amount is None:
                        _logger.warning(f"[WARN] Quy tắc [{rule.code}] {rule.name} không trả về giá trị (amount=None)")
                        amount = 0.0

                    # Log kết quả
                    if amount != 0:
                        _logger.info(f"[OK] Kết quả: {amount:,.2f} VNĐ")
                    else:
                        _logger.info(f"[SKIP] Kết quả: 0 VNĐ (không áp dụng)")
                    
                    # Lưu kết quả
                    rules[rule.code] = amount

                    # Tạo dòng chi tiết
                    lines_to_create.append({
                        'payslip_id': payslip.id,
                        'rule_id': rule.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category': rule.category,
                        'sequence': rule.sequence,
                        'amount': amount,
                        'appears_on_payslip': rule.appears_on_payslip,
                    })

                except Exception as e:
                    # Dùng ký tự ASCII thuần để tránh UnicodeEncodeError
                    _logger.error(f"[ERR] Lỗi khi tính quy tắc [{rule.code}] {rule.name}: {e}")
                    raise UserError(
                        f'Lỗi khi tính toán quy tắc "{rule.name}" (Code: {rule.code}):\n\n{e}'
                    )

            
            # Tạo tất cả dòng chi tiết
            self.env['payroll.payslip.line'].create(lines_to_create)
            
            # Log tổng kết
            _logger.info("="*60)
            _logger.info("KẾT QUẢ TÍNH LƯƠNG:")
            _logger.info(f"Lương cơ bản: {payslip.basic_wage:,.0f} VNĐ")
            _logger.info(f"Tổng phụ cấp: {payslip.total_allowance:,.0f} VNĐ")
            _logger.info(f"Tổng thu nhập (Gross): {payslip.gross_wage:,.0f} VNĐ")
            _logger.info(f"BHXH (8%): {payslip.bhxh_amount:,.0f} VNĐ")
            _logger.info(f"BHYT (1.5%): {payslip.bhyt_amount:,.0f} VNĐ")
            _logger.info(f"BHTN (1%): {payslip.bhtn_amount:,.0f} VNĐ")
            _logger.info(f"Thuế TNCN: {payslip.personal_income_tax:,.0f} VNĐ")
            _logger.info(f"Tổng khấu trừ: {payslip.total_deduction:,.0f} VNĐ")
            _logger.info(f"THỰC NHẬN (Net): {payslip.net_wage:,.0f} VNĐ")
            _logger.info("="*60)
            
            # Gửi thông báo vào chatter
            payslip.message_post(
                body=f'✅ Đã tính toán lại phiếu lương<br/>'
                     f'Lương cơ bản: {payslip.basic_wage:,.0f} VNĐ<br/>'
                     f'Tổng thu nhập: {payslip.gross_wage:,.0f} VNĐ<br/>'
                     f'Thực nhận: <b>{payslip.net_wage:,.0f} VNĐ</b>'
            )
    
    @api.depends('line_ids.amount')
    def _compute_totals(self):
        for payslip in self:
            payslip.basic_wage = sum(payslip.line_ids.filtered(lambda l: l.category == 'basic').mapped('amount'))
            payslip.total_allowance = sum(payslip.line_ids.filtered(lambda l: l.category == 'allowance').mapped('amount'))
            payslip.gross_wage = sum(payslip.line_ids.filtered(lambda l: l.category == 'gross').mapped('amount'))
            payslip.total_deduction = abs(sum(payslip.line_ids.filtered(lambda l: l.category == 'deduction').mapped('amount')))
            payslip.net_wage = sum(payslip.line_ids.filtered(lambda l: l.category == 'net').mapped('amount'))
            
            payslip.bhxh_amount = abs(sum(payslip.line_ids.filtered(lambda l: l.code == 'BHXH').mapped('amount')))
            payslip.bhyt_amount = abs(sum(payslip.line_ids.filtered(lambda l: l.code == 'BHYT').mapped('amount')))
            payslip.bhtn_amount = abs(sum(payslip.line_ids.filtered(lambda l: l.code == 'BHTN').mapped('amount')))
            payslip.total_insurance = payslip.bhxh_amount + payslip.bhyt_amount + payslip.bhtn_amount
            
            payslip.personal_income_tax = abs(sum(payslip.line_ids.filtered(lambda l: l.code == 'PIT').mapped('amount')))
    
    def action_payslip_verify(self):
        self.write({'state': 'verify'})
        for payslip in self:
            payslip.message_post(body='📋 Phiếu lương đã gửi xác nhận')
    
    def action_payslip_done(self):
        self.write({'state': 'done', 'date_payment': fields.Date.today()})
        for payslip in self:
            # Cập nhật lương hiện tại cho nhân viên
            payslip.employee_id._compute_current_salary()
            
            payslip.employee_id.message_post(
                body=f"✅ Phiếu lương {payslip.name} đã xác nhận<br/>"
                     f"Kỳ: {payslip.date_from:%d/%m/%Y} - {payslip.date_to:%d/%m/%Y}<br/>"
                     f"Thực nhận: {payslip.net_wage:,.0f} VNĐ"
            )
            payslip.message_post(body='✅ Phiếu lương đã hoàn thành')
    
    def action_payslip_draft(self):
        self.write({'state': 'draft'})
    
    def action_payslip_cancel(self):
        self.write({'state': 'cancel'})