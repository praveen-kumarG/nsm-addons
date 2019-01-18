# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class CreditControlRun(models.Model):
    _inherit = "credit.control.run"

    @api.multi
    @api.returns('credit.control.line')
    def _mark_credit_line_as_letter(self, lines):
        lines = lines.filtered(lambda p: not p.partner_id.email)
        lines.write({'channel': 'letter'})
        return lines

    @api.multi
    @api.returns('credit.control.line')
    def _generate_credit_lines(self):
        generated = super(CreditControlRun, self)._generate_credit_lines()
        self._mark_credit_line_as_letter(generated)
        return generated
