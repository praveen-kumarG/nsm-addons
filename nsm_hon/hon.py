# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2016 Magnus www.magnus.nl
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


from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class hon_issue(orm.Model):

    _name = "hon.issue"

    _columns = {
        'main_account_analytic_id': fields.many2one('account.analytic.account', 'Tijdschrift/Nummer', domain=[('type','=','view'), ('portal_main', '=', True)]),
        'number': fields.char('Uitgave Nr.', size=64, select=True ),
        'company_id': fields.many2one('res.company', 'Company', required=True, change_default=True, readonly=True, states={'draft':[('readonly',False)]}),
        'hon_line': fields.one2many('hon.line', 'hon_id', 'Hon Lines', readonly=True, states={'draft':[('readonly',False)]}),
        'state': fields.selection([
            ('draft','Draft'),
            ('open','Open'),
            ('cancel','Cancelled'),
            ],'Status', select=True, readonly=True,
            help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Honorarium Issue. \
            \n* The \'Open\' status is used when user create invoice.\
            \n* The \'Cancelled\' status is used when user cancel Honorarium Issue.'),
        'comment': fields.text('Additional Information'),
    }

    _defaults = {
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'hon', context=c),
        'state': 'draft',
    }



class hon_line(orm.Model):

    _name = "hon.line"

    _columns = {
        'sequence': fields.integer('Sequence', help="Gives the sequence of this line when displaying the invoice."),
        'name': fields.text('Description', required=True),
        'hon_id': fields.many2one('hon.issue', 'Issue Reference', ondelete='cascade', select=True),
        'employee': fields.boolean('OB Employee', states={'draft':[('readonly',False)]}, help="Checking disables Freelancer and enables Employee field"),
        'employee_id': fields.many2one('hr.employee', "Employee"),
        'partner_id': fields.many2one('res.partner', 'Partner',),
        'product_category_id': fields.many2one('product.category', 'Pagina Soort',domain=[('parent_id.supportal', '=', True)]),
        'product_id': fields.many2one('product.product', 'Product', required=True, ondelete='set null', select=True),
        'account_id': fields.many2one('account.account', 'Account', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')],
                                      help="The income or expense account related to the selected product."),
        'uos_id': fields.many2one('product.uom', 'Unit of Measure', ondelete='set null', select=True),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
        'quantity': fields.float('Quantity', digits_compute= dp.get_precision('Product Unit of Measure'), required=True),
        'account_analytic_id': fields.related('hon_id', 'account_analytic_id', type='many2one',relation='account.analytic.account', string='Tijdschrift/Nummer', store=True, readonly=True),
        'company_id': fields.related('hon_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
    }

    def _default_account_id(self, cr, uid, context=None):
        # XXX this gets the default account for the user's company,
        # it should get the default account for the invoice's company
        # however, the invoice's company does not reach this point
        if context is None:
            context = {}
        prop = self.pool.get('ir.property').get(cr, uid, 'property_account_expense_categ', 'product.category', context=context)
        return prop and prop.id or False

    _defaults = {
        'quantity': 1,
        'sequence': 10,
        #'price_unit': _price_unit_default,
        'account_id': _default_account_id,
    }

    def product_id_change(self, cr, uid, ids, product, uom_id, qty=0, name='', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None):
        if context is None:
            context = {}
        company_id = company_id if company_id != None else context.get('company_id',False)
        context = dict(context)
        context.update({'company_id': company_id, 'force_company': company_id})
        if not partner_id and not employee:
            raise osv.except_osv(_('No Employee and No Partner Defined!'),_("You must first select a partner or select Employee!") )
        if not product:
            raise osv.except_osv(_('No Product Defined!'),_("You must first select a Product!") )
        part = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
        product_uom_obj = self.pool.get('product.uom')
        fpos_obj = self.pool.get('account.fiscal.position')
        fpos = fposition_id and fpos_obj.browse(cr, uid, fposition_id, context=context) or False

        if part.lang:
            context.update({'lang': part.lang})
        result = {}
        res = self.pool.get('product.product').browse(cr, uid, product, context=context)

        a = res.property_account_expense.id
        if not a:
            a = res.categ_id.property_account_expense_categ.id
        a = fpos_obj.map_account(cr, uid, fpos, a)
        if a:
            result['account_id'] = a

        taxes = res.supplier_taxes_id and res.supplier_taxes_id or (a and self.pool.get('account.account').browse(cr, uid, a, context=context).tax_ids or False)
        tax_id = fpos_obj.map_tax(cr, uid, fpos, taxes)

        result.update( {'price_unit': price_unit or res.standard_price,'invoice_line_tax_id': tax_id} )
        result['name'] = res.partner_ref

        result['uos_id'] = res.uom_id.id
        if uom_id:
            uom = product_uom_obj.browse(cr, uid, uom_id)
            if res.uom_id.category_id.id == uom.category_id.id:
                result['uos_id'] = uom_id

        result['name'] += '\n'+res.description_purchase

        domain = {'uos_id':[('category_id','=',res.uom_id.category_id.id)]}

        res_final = {'value':result, 'domain':domain}

        if not company_id or not currency_id:
            return res_final

        company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
        currency = self.pool.get('res.currency').browse(cr, uid, currency_id, context=context)

        if company.currency_id.id != currency.id:
            res_final['value']['price_unit'] = res.standard_price
            new_price = res_final['value']['price_unit'] * currency.rate
            res_final['value']['price_unit'] = new_price

        if result['uos_id'] and result['uos_id'] != res.uom_id.id:
            selected_uom = self.pool.get('product.uom').browse(cr, uid, result['uos_id'], context=context)
            new_price = self.pool.get('product.uom')._compute_price(cr, uid, res.uom_id.id, res_final['value']['price_unit'], result['uos_id'])
            res_final['value']['price_unit'] = new_price
        return res_final

