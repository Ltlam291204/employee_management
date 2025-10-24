# -*- coding: utf-8 -*-
{
    'name': "Quản lý Nhân viên",
    'version': '18.0.2.0.0',
    'summary': 'Hệ thống quản lý nhân viên toàn diện: Hồ sơ, Hợp đồng, Bảng lương',
    'description': """
        Module quản lý nhân viên hoàn chỉnh:
        - Quản lý hồ sơ nhân viên
        - Quản lý hợp đồng lao động
        - Quản lý bảng lương và phiếu lương
        - Tính toán lương theo quy định VN: BHXH 8%, BHYT 1.5%, BHTN 1%, Thuế TNCN
        - Phân quyền: Nhân viên, Cán bộ, Giám đốc
        - Tự động tạo User khi tạo nhân viên
        - Tích hợp hoàn toàn giữa các module
    """,
    'author': "Your Company",
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'mail'],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/employee_sequence.xml',
        'data/contribution_type_data.xml',
        'data/default_salary_structure.xml',
        
        # Wizards
        'views/reset_password_wizard_views.xml',
        'views/contract_renew_wizard_views.xml',
        
        # Views
        'views/employee_views.xml',
        'views/contract_views.xml',
        'views/payroll_structure_views.xml',
        'views/payroll_payslip_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}