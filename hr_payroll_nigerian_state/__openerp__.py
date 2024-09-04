#-*- coding:utf-8 -*-
# Part of ChamsERP. See LICENSE file for full copyright and licensing details.

{
    'name': 'Nigerian Civil Service Payroll',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 38,
    'description': """
    Payroll for a Nigerian State
    """,
    'website': 'http://www.chamsplc.com',
    'depends': [
        'hr',
        'hr_contract_state',
        'hr_transfer',
        'report_xlsx',
        'web_digital_sign',
    ],
    'external_dependencies': {
        'python': ['dateutil'],
    },
    'data': [
        'security/ir.model.access.csv',
        'module_data.xml',                
        'hr_payroll_view.xml',
        'hr_disciplinary_cron.xml',
        'payroll_cron.xml',
        'init_earn_dedt_cron.xml',
        'resolve_earn_dedt_cron.xml',
        'hr_disciplinary_workflow.xml',
        'hr_demise_cron.xml',
        'hr_demise_workflow.xml',
        'hr_query_cron.xml',
        'hr_query_workflow.xml',
        'hr_retirement_cron.xml',
        'hr_retirement_workflow.xml',
        'hr_promotion_cron.xml',
        'hr_promotion_cron_auto.xml',
        'hr_promotion_cron_next.xml',
        'hr_promotion_workflow.xml',
        'security/hr_security.xml',
        'views/payroll_report.xml',
        'views/payroll_summary_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
