# -*- coding: utf-8 -*-
{
    'name': 'Order to Cash Automation',
    'version': '19.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Order Source tracking, customer duplicate check, payment matching, '
               'overdue alerts, and Order-to-Cash dashboards',
    'description': """
Order to Cash Automation
=========================
Implements the Order-to-Cash workflow discussed with the client:

* Order Source / Sales Channel on every Sales Order (Online Retail, Online
  Wholesale, Administration, Sales Team), auto-classified from the unit of
  measure used on the order lines.
* Phone-first customer duplicate check before a new contact is created.
* Automatic overdue tiering on invoices (Due Soon / Due Today / 1-7 / 8-15 /
  15+ days overdue) with a daily scheduled job that creates follow-up
  activities.
* Payment-matching guardrail: auto-reconciles a payment only when there is
  exactly one clear matching invoice; otherwise flags it for human review
  instead of guessing.
* Two lightweight reporting dashboards (Sales by Channel, Receivables Aging)
  built on native pivot/graph views.

See README.md in this module for the version target, install steps, and a
manual test checklist before you demo this to a client.
""",
    'author': 'Abdullah Khursheed',
    'license': 'LGPL-3',
    'depends': ['sale_management', 'account', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'wizards/customer_lookup_wizard_views.xml',
        'views/sale_order_views.xml',
        'views/res_partner_views.xml',
        'views/account_payment_views.xml',
        'views/account_move_views.xml',
        'views/o2c_dashboard_views.xml',
        'views/menus.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
