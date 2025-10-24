# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

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
                                   readonly=True, states={'draft': [('readonly', False)]})
    
    structure_id = fields.Many2one('payroll.structure', 'Cấu trúc lương',
                                    required=True, readonly=True,
                                    states={'draft': [('readonly', False)]})
    
    date_from = fields.Date('Từ ngày', required=True, readonly=True,
                             states={'draft': [('readonly', False)]})
    date_to = fields.Date('Đến ngày', required=True, readonly=True,
                           states={'draft': [('readonly', False)]})
    
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
    
    @api.onchange('employee_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        """Tự động lấy contract khi chọn nhân viên"""
        if self.employee_id:
            # Tìm hợp đồng đang hoạt động của nhân viên
            contract = self.env['employee.management.contract'].search([
                ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'open'),
                ('date_start', '<=', self.date_to or fields.Date.today()),
                '|', ('date_end', '=', False), ('date_end', '>=', self.date_from or fields.Date.today())
            ], limit=1, order='date_start desc')
            
            # Tự động gán contract nếu tìm được
            if contract:
                self.contract_id = contract
            
            # Nếu chưa chọn cấu trúc lương, tự động chọn cấu trúc VN
            if not self.structure_id:
                structure = self.env['payroll.structure'].search([('code', '=', 'VN_SALARY')], limit=1)
                if structure:
                    self.structure_id = structure
    
    def action_compute_sheet(self):
        """Tính toán phiếu lương - chỉ từ rule is_active=True"""
        for payslip in self:
            if not payslip.contract_id:
                raise UserError('Nhân viên không có hợp đồng đang hoạt động!')
            
            if not payslip.structure_id:
                raise UserError('Vui lòng chọn cấu trúc lương!')
            
            payslip.line_ids.unlink()
            
            rules = {}
            lines_to_create = []
            
            for rule in payslip.structure_id.rule_ids.filtered(lambda r: r.is_active).sorted('sequence'):
                amount = rule.compute_rule(
                    contract=payslip.contract_id,
                    employee=payslip.employee_id,
                    payslip=payslip,
                    rules=rules
                )
                
                rules[rule.code] = amount
                
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
            
            self.env['payroll.payslip.line'].create(lines_to_create)
            payslip.message_post(body='✅ Đã tính toán lại phiếu lương')
    
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