# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class O2CSalesDashboard(models.Model):
    """Read-only reporting view over sale.order, grouped by Order Source.
    Built as a SQL view (the same pattern Odoo's own sale.report uses) so
    the native pivot/graph/list views stay fast and don't need any custom
    frontend code."""
    _name = 'o2c.sales.dashboard'
    _description = 'O2C: Sales by Channel'
    _auto = False
    _order = 'date_order desc'

    name = fields.Char(string='Order', readonly=True)
    date_order = fields.Datetime(string='Order Date', readonly=True)
    x_order_source = fields.Selection([
        ('online_retail', 'Online Retail'),
        ('online_wholesale', 'Online Wholesale'),
        ('administration', 'Administration'),
        ('sales_team', 'Sales Team'),
    ], string='Order Source', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    state = fields.Selection([
        ('draft', 'Quotation'), ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'), ('cancel', 'Cancelled'),
    ], string='Status', readonly=True)
    amount_total = fields.Monetary(string='Total', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    so.id            AS id,
                    so.name          AS name,
                    so.date_order    AS date_order,
                    so.x_order_source AS x_order_source,
                    so.partner_id    AS partner_id,
                    so.user_id       AS user_id,
                    so.state         AS state,
                    so.amount_total  AS amount_total,
                    so.currency_id   AS currency_id
                FROM sale_order so
            )
        """ % self._table)


class O2CReceivablesDashboard(models.Model):
    """Read-only reporting view over posted customer invoices, with the
    Overdue Tier already computed on account.move so aging buckets are
    consistent everywhere they're shown."""
    _name = 'o2c.receivables.dashboard'
    _description = 'O2C: Receivables Aging'
    _auto = False
    _order = 'invoice_date_due asc'

    name = fields.Char(string='Invoice', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    invoice_date = fields.Date(string='Invoice Date', readonly=True)
    invoice_date_due = fields.Date(string='Due Date', readonly=True)
    amount_total = fields.Monetary(string='Total', readonly=True)
    amount_residual = fields.Monetary(string='Outstanding', readonly=True)
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'), ('in_payment', 'In Payment'),
        ('paid', 'Paid'), ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
    ], string='Payment Status', readonly=True)
    x_overdue_tier = fields.Selection([
        ('not_due', 'Not Due'), ('due_soon', 'Due Soon'), ('due_today', 'Due Today'),
        ('overdue_1_7', 'Overdue 1-7 Days'), ('overdue_8_15', 'Overdue 8-15 Days'),
        ('overdue_15_plus', 'Overdue 15+ Days'), ('paid', 'Paid'),
    ], string='Aging Tier', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)
    invoice_user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    am.id               AS id,
                    am.name             AS name,
                    am.partner_id       AS partner_id,
                    am.invoice_date     AS invoice_date,
                    am.invoice_date_due AS invoice_date_due,
                    am.amount_total     AS amount_total,
                    am.amount_residual  AS amount_residual,
                    am.payment_state    AS payment_state,
                    am.x_overdue_tier   AS x_overdue_tier,
                    am.currency_id      AS currency_id,
                    am.invoice_user_id  AS invoice_user_id
                FROM account_move am
                WHERE am.move_type = 'out_invoice' AND am.state = 'posted'
            )
        """ % self._table)
