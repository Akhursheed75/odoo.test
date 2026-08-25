# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_customer_type = fields.Selection([
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
        ('admin_referred', 'Admin Referred'),
        ('sales_referred', 'Sales Referred'),
    ], string='Customer Type',
        help='Optional. Only useful if you need reporting broken down by '
             'customer type in addition to Order Source.')

    @api.model
    def o2c_find_duplicates(self, phone=None, name=None, limit=10):
        """Phone-first, name-second duplicate lookup.

        Matches on the last 7 digits of the phone/mobile field so that
        formatting differences (+92 vs 0-prefix, spaces, dashes) don't cause
        false negatives. Falls back to a name search only if no phone match
        is found (or no phone was given).
        """
        matches = self.browse()
        if phone:
            digits = ''.join(ch for ch in phone if ch.isdigit())
            tail = digits[-7:] if len(digits) >= 7 else digits
            if tail:
                matches = self.search([
                    '|', ('phone', 'like', tail), ('mobile', 'like', tail),
                ], limit=limit)
        if not matches and name:
            matches = self.search([('name', 'ilike', name)], limit=limit)
        return matches
