# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = ["sale.order"]

    package = fields.Boolean(string='Package', index=True, copy=False)
    package_description = fields.Char(string='Package Description', copy=False)