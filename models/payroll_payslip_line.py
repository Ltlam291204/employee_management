# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PayrollPayslipLine(models.Model):
    _name = 'payroll.payslip.line'
    _description = 'Dòng chi tiết phiếu lương'
    _order = 'sequence, id'

    payslip_id = fields.Many2one('payroll.payslip', 'Phiếu lương', required=True, ondelete='cascade')
    rule_id = fields.Many2one('payroll.salary.rule', 'Quy tắc')
    
    name = fields.Char('Mô tả', required=True)
    code = fields.Char('Mã', required=True)
    category = fields.Selection([
        ('basic', 'Lương cơ bản'),
        ('allowance', 'Phụ cấp'),
        ('gross', 'Tổng thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('net', 'Thực nhận'),
        ('other', 'Khác'),
    ], string='Loại', required=True)
    
    sequence = fields.Integer('Thứ tự', default=100)
    amount = fields.Monetary('Số tiền', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='payslip_id.currency_id', store=True)
    
    appears_on_payslip = fields.Boolean('Hiển thị', default=True)
    note = fields.Text('Ghi chú')
    
    @api.model
    def create(self, vals):
        result = super().create(vals)
        if result.payslip_id:
            result.payslip_id._compute_totals()
        return result
    
    def unlink(self):
        payslips = self.mapped('payslip_id')
        result = super().unlink()
        for payslip in payslips:
            payslip._compute_totals()
        return result
    
    def write(self, vals):
        result = super().write(vals)
        payslips = self.mapped('payslip_id')
        for payslip in payslips:
            payslip._compute_totals()
        return result