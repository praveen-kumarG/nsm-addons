# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time

from openerp import netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

class hr_expense_expense(osv.osv):
    _inherit = 'hr.expense.expense'
    
    current_user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
    if account.group_account_invoice is in current_user.group_id/id:
        _columns = {
            'line_ids': fields.one2many('hr.expense.line', 'expense_id', 'Expense Lines', readonly=True, states={'draft':[('readonly',False)],'accepted':[('readonly',False)]}),
        
        }
    
class hr_expense_line(osv.osv):
     _inherit = 'hr.expense.line'
     
     def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        res = {}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            res['name'] = product.name
            amount_unit = product.price_get('standard_price')[product.id]
#            res['unit_amount'] = amount_unit
#            res['uom_id'] = product.uom_id.id
        return {'value': res}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
