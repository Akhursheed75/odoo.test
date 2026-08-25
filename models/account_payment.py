# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import float_is_zero


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    x_needs_match_review = fields.Boolean(
        string='Needs Match Review', default=False, copy=False,
        help='Set automatically when more than one open invoice could plausibly '
             'match this payment. Cleared once a human confirms the correct invoice.')
    x_match_note = fields.Text(
        string='Match Note', copy=False,
        help='Why this payment was auto-matched, or why it needs manual review.')

    def action_o2c_auto_match(self):
        """Button action: attempt to match/reconcile the selected payment(s)."""
        for payment in self:
            payment._o2c_attempt_match()

    @api.model
    def o2c_cron_auto_match_payments(self):
        """Scheduled action: attempt to match any posted, unreconciled inbound
        customer payment. Safe to run repeatedly — already-matched payments
        are skipped, and still-ambiguous ones are simply re-flagged."""
        domain = [
            ('state', '=', 'posted'),
            ('payment_type', '=', 'inbound'),
            ('partner_type', '=', 'customer'),
        ]
        payments = self.search(domain)
        for payment in payments:
            if hasattr(payment, 'reconciled_invoice_ids') and payment.reconciled_invoice_ids:
                continue
            payment._o2c_attempt_match()

    def _o2c_attempt_match(self):
        """Priority hierarchy (never guesses across customers):

        1. Exact invoice number / payment reference in the payment memo.
        2. Exactly one open invoice for the identified customer.
        3. Several open invoices, but exactly one matches the payment
           amount.
        4. Anything else -> flag for human review, do not touch the ledger.
        """
        self.ensure_one()
        if hasattr(self, 'reconciled_invoice_ids') and self.reconciled_invoice_ids:
            self.x_needs_match_review = False
            self.x_match_note = _('Already reconciled.')
            return

        if not self.partner_id:
            self.x_needs_match_review = True
            self.x_match_note = _('No customer identified on this payment — match manually.')
            return

        open_invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial')),
            ('partner_id', '=', self.partner_id.id),
        ])
        if not open_invoices:
            self.x_needs_match_review = True
            self.x_match_note = _('No open invoices found for this customer.')
            return

        ref = (self.ref or self.memo or '').strip() if hasattr(self, 'memo') else (self.ref or '').strip()
        if ref:
            ref_matches = open_invoices.filtered(
                lambda inv: ref in (inv.name or '') or ref in (inv.payment_reference or '')
            )
            if len(ref_matches) == 1:
                self._o2c_reconcile(ref_matches)
                return

        if len(open_invoices) == 1:
            self._o2c_reconcile(open_invoices)
            return

        amount_matches = open_invoices.filtered(
            lambda inv: float_is_zero(inv.amount_residual - self.amount, precision_digits=2)
        )
        if len(amount_matches) == 1:
            self._o2c_reconcile(amount_matches)
            return

        self.x_needs_match_review = True
        self.x_match_note = _(
            '%(count)d open invoices found for this customer — confirm the correct one manually.'
        ) % {'count': len(open_invoices)}

    def _o2c_reconcile(self, invoices):
        """Reconcile this payment's receivable line against the given invoice(s)'
        receivable line(s) using Odoo's own reconciliation engine — the same
        mechanism the bank-reconciliation widget uses internally."""
        self.ensure_one()
        payment_lines = self.move_id.line_ids.filtered(
            lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
        )
        invoice_lines = invoices.line_ids.filtered(
            lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
        )
        if not payment_lines or not invoice_lines:
            self.x_needs_match_review = True
            self.x_match_note = _('Could not find an open receivable line to reconcile — check manually.')
            return
        (payment_lines + invoice_lines).reconcile()
        self.x_needs_match_review = False
        self.x_match_note = _('Auto-matched to %s') % ', '.join(invoices.mapped('name'))
