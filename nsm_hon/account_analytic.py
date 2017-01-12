# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2016 Magnus www.magnus.nl w.hulshof@magnus.nl
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

from openerp.osv import osv
from openerp.osv import fields

class account_analytic(osv.osv):
    _inherit = 'account.analytic.account'

    def _supplier_analytic_search(self, cr, uid, obj, name, args,  context=None):
        if not args or not isinstance(args[0][2], (int, long)) or not args[0][2]:
            return [('id', '=', False)]  # maybe raise NotImplemented?
        user = self.pool['res.users'].browse(cr, uid, args[0][2], context=context)
        supplier = user.partner_id  # partner_id is required on users
        if not supplier.analytic_account_ids:
            return [('id', '=', False)]
        acc_ids = [acc.id for acc in supplier.analytic_account_ids]
        return [('id', 'in', acc_ids)]

    _columns = {
            'supp_analytic_accids': fields.function(lambda self, cr, uid, ids, field_name, arg, context=None: dict.fromkeys(ids, True), fnct_search=_supplier_analytic_search, type='integer', method=True,),
    }


account_analytic()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
