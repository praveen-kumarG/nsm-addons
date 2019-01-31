# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Eurogroup Consulting NL (<http://eurogroupconsulting.nl>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from odoo import models, fields, api, _

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        if self.type in ('in_invoice', 'in_refund'):
            self.user_id = self.env.user
        return res

    @api.multi
    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        for inv in self:
            if 'invoice_line_ids' in vals:
                if inv.type in ('in_invoice', 'in_refund'):
                    invoice_line = inv.invoice_line_ids and inv.invoice_line_ids[0]
                    if invoice_line.account_analytic_id:
                        team_acc_mapp = self.env['sales.team'].search([('analytic_account_id','=',invoice_line.account_analytic_id.id)], limit=1)
                        if team_acc_mapp and team_acc_mapp.sales_team_id:
                            inv.team_id = team_acc_mapp.sales_team_id.id
        return res

