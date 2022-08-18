# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date, datetime
import json

class PosSession(models.Model):
    _inherit = 'pos.session'

    info_amounts = fields.Text(compute="_compute_info_amounts")

    @api.depends('payment_method_ids', 'cash_register_balance_start', 'cash_register_id')
    def _compute_info_amounts(self):
        self.get_amounts_payments()

    def get_amounts_payments(self):
        for session in self:
            payments_session = self.env['pos.payment'].search([('session_id', '=', session.id)])
            array = []
            if payments_session:

                query = """ select 
                               ppp.id as ide, ppp."name", sum(pp.amount) as total
                               from pos_payment pp inner join pos_payment_method ppp on pp.payment_method_id = ppp."id"
                               where pp.id """
                if len(payments_session.ids) > 1:
                    ids = tuple(payments_session.ids)
                    query += """  in {0} """.format(ids)
                else:
                    id = payments_session.id
                    query += """  = {0} """.format(id)
                query += """ group by ppp.id, ppp.name"""

                self.env.cr.execute(query)
                q = self.env.cr.fetchall()
                if q:
                    for res in q:
                        data_json = {
                            'ide': res[0],
                            'name': res[1],
                            'total': res[2],
                            'session_id': session.id,
                        }
                        array.append(data_json)
            session.info_amounts = json.dumps(array)
        return array

    def print_report_close_cash(self):
        datas = {'ids': self.id,
                 'model': 'pos.session'
                 }
        return self.env.ref('aspl_pos_close_session.pos_z_report').report_action(self.id)


    def get_amount_total(self):
        amount_total = 0.0
        if self:
            if self.order_ids:
                amount_total = sum(o.amount_total for o in self.order_ids)

        return amount_total

    def get_amount_total_sn_taxt(self):
        amount_total = 0.0
        if self:
            if self.order_ids:
                amount_total = sum(o.amount_total - o.amount_tax for o in self.order_ids)

        return amount_total

    def get_count_sales(self):
        count = 0
        if self:
            count = len(self.order_ids)

        return count

    def get_cash_in(self):
        cash_in = 0.0
        moves_in = self.env['pos.cash.in.out'].sudo().search([('session_id', '=', self.id),('transaction_type','=','cash_in')])
        if moves_in:
            cash_in = sum(ci.amount for ci in moves_in)

        return cash_in

    def get_cash_out(self):
        cash_out = 0.0
        moves_out = self.env['pos.cash.in.out'].sudo().search([('session_id', '=', self.id), ('transaction_type', '=', 'cash_out')])
        if moves_out:
            cash_out = sum(co.amount for co in moves_out)

        return cash_out

    def get_amount_total_tax(self):
        amount_tax = 0.0
        if self:
            if self.order_ids:
                amount_tax = sum(o.amount_tax for o in self.order_ids)

        return amount_tax

    def get_amount_total_reserved(self):
        amount_paid = 0.0
        if self:
            if self.order_ids:
                o_reserved = self.order_ids.filtered(lambda r:r.state == 'reserved')
                amount_paid = sum(o.amount_paid for o in o_reserved)

        return amount_paid