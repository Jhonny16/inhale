# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
from datetime import datetime, date, timedelta
from odoo import models, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import pytz
import logging
from pytz import timezone

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'


    def get_gross_total_currency(self, currency_id):
        gross_total = 0.0
        orders = self.order_ids.filtered(lambda o: o.currency_id.id == currency_id.id)
        if self and orders:
            for order in orders:
                for line in order.lines:
                    gross_total += line.qty * (line.price_unit - line.product_id.standard_price)
        return gross_total

    def get_net_gross_total_currency(self, currency_id):
        net_gross_profit = 0.0
        if self:
            net_gross_profit = self.get_gross_total_currency(currency_id) - self.get_total_tax_currency(currency_id)
        return net_gross_profit

    def get_total_sales_currency(self, currency_id):
        total_price = 0.0
        if self:
            orders = self.order_ids.filtered(lambda o: o.currency_id.id == currency_id.id)
            for order in orders:
                total_price += sum([(line.qty * line.price_unit) for line in order.lines])
        return total_price

    def exists_orders_currency(self, currency_id):
        orders = self.order_ids.filtered(lambda o: o.currency_id.id == currency_id.id)
        if orders:
            return True
        else:
            return False

    def get_total_tax_currency(self, currency_id):
        if self:
            total_tax = 0.0
            #pos_order_obj = self.env['pos.order']
            #total_tax += sum([order.amount_tax for order in pos_order_obj.search([('session_id', '=', self.id),('currency_id','=',currency_id.id)])])
            orders = self.order_ids.filtered(lambda o: o.currency_id.id == currency_id.id)
            total_tax += sum([order.amount_tax for order in orders])
        return total_tax

    def get_vat_tax_currency(self, currency_id):
        taxes_info = []
        if self:
            orders = self.order_ids.filtered(lambda o: o.currency_id.id == currency_id.id)            
            tax_list = [tax.id for order in orders for line in
                        order.lines.filtered(lambda line: line.tax_ids_after_fiscal_position) for tax in
                        line.tax_ids_after_fiscal_position]
            tax_list = list(set(tax_list))
            for tax in self.env['account.tax'].browse(tax_list):
                total_tax = 0.00
                net_total = 0.00
                for line in self.env['pos.order.line'].search(
                        [('order_id', 'in', [order.id for order in orders])]).filtered(
                    lambda line: tax in line.tax_ids_after_fiscal_position):
                    total_tax += line.price_subtotal * tax.amount / 100
                    net_total += line.price_subtotal
                taxes_info.append({
                    'tax_name': tax.name,
                    'tax_total': total_tax,
                    'tax_per': tax.amount,
                    'net_total': net_total,
                    'gross_tax': total_tax + net_total
                })
        return taxes_info

    def get_total_discount_currency(self,currency_id):
        total_discount = 0.0
        orders = self.order_ids.filtered(lambda o: o.currency_id.id == currency_id.id)
        if self and orders:
            for order in orders:
                total_discount += sum([((line.qty * line.price_unit) * line.discount) / 100 for line in order.lines])
        return total_discount

    def get_total_first_currency(self, currency_id):
        total = 0.0
        if self:
            total = (self.get_total_sales_currency(currency_id) + self.get_total_tax_currency(currency_id)) \
                    - (abs(self.get_total_discount_currency(currency_id)))
        return total


    def get_product_category_currency(self, currency_id):
        product_list = []
        orders = self.order_ids.filtered(lambda o: o.currency_id.id == currency_id.id)
        if self and orders:
            for order in orders:
                for line in order.lines:
                    flag = False
                    product_dict = {}
                    for lst in product_list:
                        if line.product_id.pos_categ_id:
                            if lst.get('pos_categ_id') == line.product_id.pos_categ_id.id:
                                lst['price'] = lst['price'] + (line.qty * line.price_unit)
                                flag = True
                        else:
                            if lst.get('pos_categ_id') == '':
                                lst['price'] = lst['price'] + (line.qty * line.price_unit)
                                flag = True
                    if not flag:
                        product_dict.update({
                            'pos_categ_id': line.product_id.pos_categ_id and line.product_id.pos_categ_id.id or '',
                            'price': (line.qty * line.price_unit)
                        })
                        product_list.append(product_dict)
        return product_list

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
