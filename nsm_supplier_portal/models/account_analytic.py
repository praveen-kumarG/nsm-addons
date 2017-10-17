# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2014 BAS Solutions
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

from odoo import api, fields, models, _

class Analytic(models.Model):
    _inherit = 'account.analytic.account'

    @api.multi
    @api.depends('name')
    def name_get(self):
        result = []
        for case in self:
            result.append((case.id, case.name))
        return result

    def _supplier_analytic_search(self, operator, value):
        # TODO: FIXME Test with 7
        supplier = self.env.user.partner_id
        if not supplier.analytic_account_ids:
            return [('id', '=', False)]
        return [('id', 'in', supplier.analytic_account_ids.ids)]


    portal_main = fields.Boolean('Portal Main')
    portal_sub = fields.Boolean('Portal Sub')
    supp_analytic_accids = fields.Integer(compute=lambda self, cr, uid, ids, field_name, arg, context=None: dict.fromkeys(ids, True),
                                           search=_supplier_analytic_search)


    @api.onchange('portal_main', 'portal_sub')
    def onchange_portal(self, portal_main, portal_sub, field):
        if portal_main and portal_sub:
            return {'warning': {
                'title': _('Portal Warning!'),
                'message': _('You can not use same analytic account for '
                             'Main portal as well as Sub portal')},
                'value': {field:False
                          }
            }
        return {}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
