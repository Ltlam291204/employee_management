# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PayrollStructure(models.Model):
    _name = 'payroll.structure'
    _description = 'Cấu trúc lương'
    _order = 'sequence, name'

    name = fields.Char('Tên cấu trúc', required=True)
    code = fields.Char('Mã', required=True)
    sequence = fields.Integer('Thứ tự', default=10)
    active = fields.Boolean('Hoạt động', default=True)
    note = fields.Text('Ghi chú')
    category = fields.Char(string='Category')
    is_active = fields.Boolean(string="Hoạt động", default=True) 
    # Hiển thị tất cả rule (không dùng active field mặc định)
    rule_ids = fields.One2many('payroll.salary.rule', 'structure_id', 'Quy tắc lương')
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã cấu trúc phải là duy nhất!')
    ]