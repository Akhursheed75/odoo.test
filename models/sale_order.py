# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

ORDER_SOURCE_SELECTION = [
    ('online_retail', 'Online Retail'),
    ('online_wholesale', 'Online Wholesale'),
    ('administration', 'Administration'),
    ('sales_team', 'Sales Team'),
]

# Heuristic used to auto-classify Retail vs Wholesale: if any order line's
# unit of measure name contains one of these words, the order is treated as
# Wholesale. Adjust this list (or replace with a proper UoM category check)
# to match the client's actual "Carton" UoM name once confirmed.
CARTON_UOM_KEYWORDS = ('carton', 'box', 'case')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_order_source = fields.Selection(
        ORDER_SOURCE_SELECTION,
        string='Order Source',
        default='online_retail',
        tracking=True,
        help='Sales channel this order came through. For online orders this '
             'is auto-set from the unit of measure used on the lines '
             '(Units -> Online Retail, Carton -> Online Wholesale). '
             'Administration and Sales Team orders are always set manually '
             'and are never overridden by the automation.',
    )

    @api.onchange('order_line')
    def _onchange_order_line_x_order_source(self):
        """Auto-classify Retail vs Wholesale from the line UoM.

        Only touches orders that are currently Online Retail / Online
        Wholesale (or unset) — an order explicitly marked Administration or
        Sales Team is never silently reclassified.
        """
        for order in self:
            if order.x_order_source not in ('online_retail', 'online_wholesale', False):
                continue
            uses_carton = any(
                any(keyword in (line.product_uom.name or '').lower() for keyword in CARTON_UOM_KEYWORDS)
                for line in order.order_line
            )
            order.x_order_source = 'online_wholesale' if uses_carton else 'online_retail'

    def action_open_customer_lookup(self):
        """Open the phone-first duplicate-check wizard for this order's customer."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Find / Verify Customer'),
            'res_model': 'o2c.customer.lookup.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_phone': self.partner_id.phone or self.partner_id.mobile if self.partner_id else False,
                'default_name': self.partner_id.name if self.partner_id else False,
            },
        }
