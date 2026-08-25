# -*- coding: utf-8 -*-
from datetime import date

from odoo import api, fields, models

OVERDUE_TIER_SELECTION = [
    ('not_due', 'Not Due'),
    ('due_soon', 'Due Soon (<= 3 days)'),
    ('due_today', 'Due Today'),
    ('overdue_1_7', 'Overdue 1-7 Days'),
    ('overdue_8_15', 'Overdue 8-15 Days'),
    ('overdue_15_plus', 'Overdue 15+ Days'),
    ('paid', 'Paid'),
    ('not_applicable', 'N/A'),
]

# Tiers that should generate/keep a follow-up activity.
ACTIONABLE_TIERS = ('due_soon', 'due_today', 'overdue_1_7', 'overdue_8_15', 'overdue_15_plus')

TIER_SUMMARY = {
    'due_soon': 'O2C: Invoice due in 3 days',
    'due_today': 'O2C: Invoice due today',
    'overdue_1_7': 'O2C: Invoice overdue 1-7 days',
    'overdue_8_15': 'O2C: Invoice overdue 8-15 days',
    'overdue_15_plus': 'O2C: Invoice overdue 15+ days',
}


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_overdue_tier = fields.Selection(
        OVERDUE_TIER_SELECTION, string='Overdue Tier',
        compute='_compute_x_overdue_tier', store=True,
        help='Recomputed daily by the "O2C: Recompute Overdue Tiers" scheduled '
             'action, since this depends on the passage of time, not just field changes.')

    @api.depends('invoice_date_due', 'payment_state', 'move_type', 'state')
    def _compute_x_overdue_tier(self):
        today = date.today()
        for move in self:
            if move.move_type != 'out_invoice' or move.state != 'posted':
                move.x_overdue_tier = 'not_applicable'
                continue
            if move.payment_state == 'paid':
                move.x_overdue_tier = 'paid'
                continue
            if not move.invoice_date_due:
                move.x_overdue_tier = 'not_due'
                continue
            delta = (move.invoice_date_due - today).days
            if delta > 3:
                move.x_overdue_tier = 'not_due'
            elif delta > 0:
                move.x_overdue_tier = 'due_soon'
            elif delta == 0:
                move.x_overdue_tier = 'due_today'
            elif delta >= -7:
                move.x_overdue_tier = 'overdue_1_7'
            elif delta >= -15:
                move.x_overdue_tier = 'overdue_8_15'
            else:
                move.x_overdue_tier = 'overdue_15_plus'

    @api.model
    def o2c_cron_recompute_overdue_tiers(self):
        """Scheduled action: recompute tiers for all open customer invoices
        and create/refresh follow-up activities. Safe to run repeatedly —
        it won't create a duplicate activity for a tier that's unchanged
        since the last run."""
        invoices = self.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial')),
        ])
        invoices._compute_x_overdue_tier()
        invoices._o2c_create_due_activities()

    def _o2c_create_due_activities(self):
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        for move in self:
            if move.x_overdue_tier not in ACTIONABLE_TIERS:
                continue
            summary = TIER_SUMMARY[move.x_overdue_tier]
            existing = self.env['mail.activity'].search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', move.id),
                ('summary', '=', summary),
            ], limit=1)
            if existing:
                continue
            move.activity_schedule(
                'mail.mail_activity_data_todo' if activity_type else False,
                summary=summary,
                note=summary,
                user_id=move.invoice_user_id.id or self.env.uid,
            )
