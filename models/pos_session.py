# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date, datetime, timedelta
import pytz
import json


class PosSession(models.Model):
    _inherit = 'pos.session'

    info_amounts = fields.Text(compute="_compute_info_amounts")

    def date_close(self):
        return (self.stop_at - timedelta(hours=5)).date()

    def get_cash_register_balance_start(self):
        currency_id = self.currency_id
        cash_register_balance_start = self.cash_register_balance_start
        if currency_id != self.company_id.currency_id:
            tc = currency_id._convert(1, self.company_id.currency_id, self.company_id, self.date_close())
            tc_start = currency_id._convert(1, self.company_id.currency_id, self.company_id, self.start_at.date())
            print("Tipo de cambio cierre: %s" % tc)
            print("Tipo de cambio apertura: %s" % tc_start)
            cash_register_balance_start = self.company_id.currency_id.round(cash_register_balance_start * tc)

        return cash_register_balance_start

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

    def get_amounts_payments_currency_company(self):
        for session in self:
            payments_session = self.env['pos.payment'].search([('session_id', '=', session.id)])
            array = []
            if payments_session:
                payment_method_ids = payments_session.mapped('payment_method_id')

                for method in payment_method_ids:
                    payments = payments_session.filtered(lambda p:p.payment_method_id.id == method.id)

                    method_amount = 0.0
                    other_amount = 0.0
                    for payment in payments:
                        currency_id = payment.currency_id
                        amount = payment.amount
                        if currency_id != self.company_id.currency_id:
                            other_currency_id = currency_id
                            other_amount += amount
                            tc = currency_id._convert(1, self.company_id.currency_id, self.company_id, self.date_close())
                            amount = amount * tc
                        method_amount += amount

                    data_json = {
                        'ide': method.id,
                        'name': method.name,
                        'total': method_amount,
                        'session_id': session.id,
                        'other_currency_id': other_currency_id,
                        'other_amount': other_amount
                    }
                    array.append(data_json)

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
                for o in self.order_ids:
                    if o.pricelist_id.currency_id != self.company_id.currency_id:
                        tc = 1/o.currency_rate
                        amount_total += tc * o.amount_total
                        #amount_total +=  o.pricelist_id.currency_id._convert(1, self.company_id.currency_id, invoice.company_id, invoice.invoice_date)
                    else:
                        amount_total += o.amount_total

                #amount_total = sum(o.amount_total for o in self.order_ids)

        return amount_total

    def get_amount_total_sn_taxt(self):
        amount_total = 0.0
        if self:
            if self.order_ids:
                #amount_total = sum(o.amount_total - o.amount_tax for o in self.order_ids)
                for o in self.order_ids:
                    if o.pricelist_id.currency_id != self.company_id.currency_id:
                        tc = 1/o.currency_rate
                        amount_total += tc * (o.amount_total - o.amount_tax)
                    else:
                        amount_total += (o.amount_total - o.amount_tax)

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
                #amount_tax = sum(o.amount_tax for o in self.order_ids)
                for o in self.order_ids:
                    if o.pricelist_id.currency_id != self.company_id.currency_id:
                        tc = 1/o.currency_rate
                        amount_tax += tc * o.amount_tax
                    else:
                        amount_tax += o.amount_tax

        return amount_tax

    def get_amount_total_reserved(self):
        amount_paid = 0.0
        if self:
            if self.order_ids:
                o_reserved = self.order_ids.filtered(lambda r:r.state == 'reserved')
                #amount_paid = sum(o.amount_paid for o in o_reserved)
                for o in o_reserved:
                    if o.pricelist_id.currency_id != self.company_id.currency_id:
                        tc = 1 / o.currency_rate
                        amount_paid += tc * o.amount_paid
                    else:
                        amount_paid += o.amount_paid

        return amount_paid

    def get_cash_register_balance_end_real(self):
        currency_id = self.currency_id
        cash_register_balance_end_real = self.cash_register_balance_end_real
        if currency_id != self.company_id.currency_id:
            tc = currency_id._convert(1, self.company_id.currency_id, self.company_id, self.date_close())
            cash_register_balance_end_real = self.company_id.currency_id.round(cash_register_balance_end_real * tc)

        return cash_register_balance_end_real

    def get_total_closing_currency_company(self):
        currency_id = self.currency_id
        cash_register_balance_end_real = self.cash_register_balance_end_real
        if currency_id != self.company_id.currency_id:
            tc = currency_id._convert(1, self.company_id.currency_id, self.company_id, self.date_close())
            cash_register_balance_end_real = self.company_id.currency_id.round(cash_register_balance_end_real * tc)

        return cash_register_balance_end_real

    def get_cash_real_difference(self):
        currency_id = self.currency_id
        cash_real_difference = self.cash_real_difference
        if currency_id != self.company_id.currency_id:
            tc = currency_id._convert(1, self.company_id.currency_id, self.company_id, self.date_close())
            cash_real_difference = self.company_id.currency_id.round(cash_real_difference * tc)

        return cash_real_difference

    def get_journal_amount_currency_company(self):
        journal_list = []
        if self.statement_ids:
            for statement in self.statement_ids:
                journal_dict = {}
                currency_id = statement.currency_id
                balance_end_real = statement.balance_end_real or 0.0
                other_amount = 0.0
                other_currency = False
                if currency_id != self.company_id.currency_id:
                    other_amount += balance_end_real
                    other_currency = currency_id
                    tc = currency_id._convert(1, self.company_id.currency_id, self.company_id, self.date_close())
                    balance_end_real = self.company_id.currency_id.round(balance_end_real * tc)

                journal_dict.update({'journal_id': statement.journal_id and statement.journal_id.name or '',
                                     'ending_bal': balance_end_real,
                                     'other_amount': other_amount,
                                     'other_currency': other_currency,
                                     })
                journal_list.append(journal_dict)
        return journal_list