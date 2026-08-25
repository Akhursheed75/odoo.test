# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class O2CCustomerLookupWizard(models.TransientModel):
    _name = 'o2c.customer.lookup.wizard'
    _description = 'O2C: Find or create a customer (phone-first duplicate check)'

    sale_order_id = fields.Many2one('sale.order', string='Sales Order')
    phone = fields.Char(string='Phone Number')
    name = fields.Char(string='Customer Name')
    match_ids = fields.Many2many('res.partner', string='Possible Matches', readonly=True)
    selected_partner_id = fields.Many2one('res.partner', string='Use This Existing Customer')
    default_payment_term_id = fields.Many2one('account.payment.term', string='Default Payment Terms (new customer)')
    searched = fields.Boolean(default=False)

    def action_search(self):
        self.ensure_one()
        matches = self.env['res.partner'].o2c_find_duplicates(phone=self.phone, name=self.name)
        self.write({
            'match_ids': [(6, 0, matches.ids)],
            'searched': True,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_use_existing(self):
        self.ensure_one()
        if not self.selected_partner_id:
            raise UserError(_('Select a customer from the list of matches first.'))
        if self.sale_order_id:
            self.sale_order_id.partner_id = self.selected_partner_id
        return {'type': 'ir.actions.act_window_close'}

    def action_create_new(self):
        self.ensure_one()
        if not self.name:
            raise UserError(_('Enter a customer name before creating a new contact.'))
        partner_vals = {
            'name': self.name,
            'phone': self.phone,
            'company_type': 'person',
        }
        if self.default_payment_term_id:
            partner_vals['property_payment_term_id'] = self.default_payment_term_id.id
        partner = self.env['res.partner'].create(partner_vals)
        if self.sale_order_id:
            self.sale_order_id.partner_id = partner
        return {'type': 'ir.actions.act_window_close'}
