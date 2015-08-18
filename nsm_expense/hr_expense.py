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
    

    _columns = {
        'line_ids': fields.one2many('hr.expense.line', 'expense_id', 'Expense Lines', readonly=True, states={'draft':[('readonly',False)],'confirm':[('readonly',False)]}),
        'account_id': fields.many2one('account.account', 'Account', readonly=True, help="The partner account used for this expense."),
        'state': fields.selection([
            ('draft', 'New'),
            ('cancelled', 'Refused'),
            ('confirm', 'Waiting Finance'),
            ('done', 'Waiting Approval'),
            ('accepted', 'Waiting Payment'),
            ('paid', 'Paid'),
            ],
            'Status', readonly=True, track_visibility='onchange',
            help='When the expense request is created the status is \'Draft\'.\n It is confirmed by the user and request is sent to Finance, the status is \'Waiting Finance\'.\
            \nIf Finance made accounting entries, the status is \'Waiting Approval\'.\n If the Manager has given approval, the status is \'Waiting Payment\'.'),

    }
    
    def action_receipt_create(self, cr, uid, ids, context=None):
        '''
        main function that is called when trying to create the accounting entries related to an expense, inherited from hr_expense
        '''
        '''
        super(hr_expense_expense, self).action_receipt_create(cr, uid, ids, context=context)
        '''
        move_obj = self.pool.get('account.move')
        for exp in self.browse(cr, uid, ids, context=context):
            if not exp.employee_id.address_home_id:
                raise osv.except_osv(_('Error!'), _('The employee must have a home address.'))
            if not exp.employee_id.address_home_id.property_account_payable.id:
                raise osv.except_osv(_('Error!'), _('The employee must have a payable account set on his home address.'))
            company_currency = exp.company_id.currency_id.id
            diff_currency_p = exp.currency_id.id <> company_currency
            
            #create the move that will contain the accounting entries
            move_id = move_obj.create(cr, uid, self.account_move_get(cr, uid, exp.id, context=context), context=context)
        
            #one account.move.line per expense line (+taxes..)
            eml = self.move_line_get(cr, uid, exp.id, context=context)
            
            #create one more move line, a counterline for the total on payable account
            total, total_currency, eml = self.compute_expense_totals(cr, uid, exp, company_currency, exp.name, eml, context=context)
            acc = exp.employee_id.address_home_id.property_account_payable.id
            eml.append({
                    'type': 'dest',
                    'name': '/',
                    'price': total, 
                    'account_id': acc, 
                    'date_maturity': exp.date_confirm, 
                    'amount_currency': diff_currency_p and total_currency or False, 
                    'currency_id': diff_currency_p and exp.currency_id.id or False, 
                    'ref': exp.name
                    })

            #convert eml into an osv-valid format
            lines = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, exp.employee_id.address_home_id, exp.date_confirm, context=context)), eml)
            journal_id = move_obj.browse(cr, uid, move_id, context).journal_id
            # post the journal entry if 'Skip 'Draft' State for Manual Entries' is checked
            if journal_id.entry_posted:
                move_obj.button_validate(cr, uid, [move_id], context)
            move_obj.write(cr, uid, [move_id], {'line_id': lines}, context=context)
            self.write(cr, uid, ids, {'account_move_id': move_id, 'account_id': acc, 'state': 'done'}, context=context)
        return True
    
    def move_line_get(self, cr, uid, expense_id, context=None):
        res = []
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        if context is None:
            context = {}
        exp = self.browse(cr, uid, expense_id, context=context)
        company_currency = exp.company_id.currency_id.id

        for line in exp.line_ids:
            mres = self.move_line_get_item(cr, uid, line, context)
            if not mres:
                continue
            res.append(mres)
            
            #Calculate tax according to default tax on product
            taxes = []
            #Taken from product_id_onchange in account.invoice
            if line.product_id:
                fposition_id = False
                fpos_obj = self.pool.get('account.fiscal.position')
                fpos = fposition_id and fpos_obj.browse(cr, uid, fposition_id, context=context) or False
                product = line.product_id
                taxes = product.supplier_taxes_id
                #If taxes are not related to the product, maybe they are in the account
                if not taxes:
                    a = product.property_account_expense.id #Why is not there a check here?
                    if not a:
                        a = product.categ_id.property_account_expense_categ.id
                    a = fpos_obj.map_account(cr, uid, fpos, a)
                    taxes = a and self.pool.get('account.account').browse(cr, uid, a, context=context).tax_ids or False
            if not taxes:
                continue
            tax_l = []
            base_tax_amount = line.total_amount
            #Calculating tax on the line and creating move?
            for tax in tax_obj.compute_all(cr, uid, taxes,
                    line.unit_amount ,
                    line.unit_quantity, line.product_id,
                    exp.user_id.partner_id)['taxes']:
                tax_code_id = tax['base_code_id']
                if not tax['amount'] and not tax['tax_code_id']:
                    continue
                res[-1]['tax_code_id'] = tax_code_id
                ## 
                is_price_include = tax_obj.read(cr,uid,tax['id'],['price_include'],context)['price_include']
                if is_price_include:
                    ## We need to deduce the price for the tax
                    res[-1]['price'] = res[-1]['price'] - tax['amount']
                    # tax amount countains base amount without the tax
                    base_tax_amount = (base_tax_amount - tax['amount']) * tax['base_sign']
                else:
                    base_tax_amount = base_tax_amount * tax['base_sign']

                assoc_tax = {
                             'type':'tax',
                             'name':tax['name'],
                             'price_unit': tax['price_unit'],
                             'quantity': 1,
                             'price': tax['amount'] or 0.0,
                             'account_id': tax['account_collected_id'] or mres['account_id'],
                             'tax_code_id': tax['tax_code_id'],
                             'tax_amount': tax['amount'] * tax['base_sign'],
                             }
                tax_l.append(assoc_tax)

            res[-1]['tax_amount'] = cur_obj.compute(cr, uid, exp.currency_id.id, company_currency, base_tax_amount, context={'date': exp.date_confirm})
            res += tax_l
        return res
    
    # Workflow stuff
    #################

    # return the ids of the move lines which has the same account than the invoice
    # whose id is in ids
    def move_line_id_payment_get(self, cr, uid, ids, *args):
        if not ids: return []
        result = self.move_line_id_payment_gets(cr, uid, ids, *args)
        return result.get(ids[0], [])

    def move_line_id_payment_gets(self, cr, uid, ids, *args):
        res = {}
        if not ids: return res
        cr.execute('SELECT i.id, l.id '\
                   'FROM account_move_line l '\
                   'LEFT JOIN hr_expense_expense i ON (i.account_move_id=l.move_id) '\
                   'WHERE i.id IN %s '\
                   'AND l.account_id=i.account_id',
                   (tuple(ids),))
        for r in cr.fetchall():
            res.setdefault(r[0], [])
            res[r[0]].append( r[1] )
        return res

    def test_paid(self, cr, uid, ids, *args):
        res = self.move_line_id_payment_get(cr, uid, ids)
        if not res:
            return False
        ok = True
        for id in res:
            cr.execute('select reconcile_id from account_move_line where id=%s', (id,))
            ok = ok and  bool(cr.fetchone()[0])
        return ok
    
    def confirm_paid(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        self.write(cr, uid, ids, {'state':'paid'}, context=context)
        return True
    
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
