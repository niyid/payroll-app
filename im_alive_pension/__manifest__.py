# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'I-am-Alive Pension Management',
    'version': '1.1',
    'category': 'Human Resources',
    'sequence': 975,
    'summary': 'I-am-Alive Pension Management',
    'description': """
I-am-Alive Pension Management
=============================

This application enables you to manage I-am-alive Pension

1. A back-end module which allows:
    1. Crediting of accounts
    2. Uploading of payment files (listing beneficiaries and amounts)
    3. Account Management Service - transaction history
    4. Direct Debit (airtime credit, etc)
2. A front-end mobile app (Android & iOS) which allows:
    1. Registration of beneficiary. This consists of the capture of the following:
        1. Face/photo
        2. Voice
        3. PIN
        4. Phone Number
        5. Secret Questions
    2. Additionally, can do a photo comparison to preexisting database during the registration phase. Once comparison is successful registration is approved (without need for entering full pensioner information).
    3. Notification when payment is pending:
        1. The beneficiary receives an in-app notification/SMS/email.
        2. He logs into the app.
        3. He is verified by video (blinking multiple times) and then voice (reading a secret phrase).
        4. Once verification is successful, payment is completed.
    """,
    'website': 'https://www.odoo.com/page/employees',
    'images': [
        'images/hr_department.jpeg',
        'images/hr_employee.jpeg',
        'images/hr_job_position.jpeg',
        'static/src/img/default_image.png',
    ],
    'depends': [
        'base_setup',
        'mail',
        'resource',
        'web_kanban',
        'hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/pension_security.xml',
        'views/pension_views.xml',
        'ddebit_cron.xml',
        'ddebit_workflow.xml',
        'enrollment_cron.xml',
        'enrollment_workflow.xml',
        'payment_cron.xml',
        'payment_workflow.xml',        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
