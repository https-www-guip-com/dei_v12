# -*- coding: utf-8 -*-
{
    'name': "CAI",
    'summary': """
           Regimen de facturacion en Honduras
        """,
    'author': "Ariel Cerrato",
    'website': "https://www.bintell.net/",
    'category': 'payroll',
    'version': '1.0',
    'license': 'OPL-1',
    'data': [
        'security/group_dei.xml',
        'security/ir.model.access.csv',
        'views/menu_principal.xml',
        'views/account_invoice.xml',
        'views/secuencia.xml',
        'views/account_config_setting_view.xml',
        "reports/facturas_print.xml",
        "reports/facturas_print_view.xml",
        
    ],
    'depends': ['account'],
    'installable': True,
    'auto_install': False,
    'application': True,
}