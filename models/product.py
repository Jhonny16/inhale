# -*- coding: utf-8 -*-

import logging
import re
from odoo import api, fields, models, tools, _
_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = "product.product"

    name_complete = fields.Char(string='Name complete', compute='_compute_name_complete', store=True)

    @api.depends('name','product_template_attribute_value_ids')
    def _compute_name_complete(self):
        for record in self:
            name_complete = record.name
            res = record.name_get()
            if type(res) == list:
                if type(res[0]) == tuple:
                    name_complete = res[0][1]

            record.name_complete = name_complete

