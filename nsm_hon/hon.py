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
        'main_account_analytic_id': fields.many2one('account.analytic.account', 'Titel/Nummer', required=True, domain=[('type','!=','view'), ('portal_sub', '=', True)]),
        #'parent_analytic_id': fields.many2one('account.analytic.account', 'Tijdschrift', required=True, ),
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
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'hon.issue', context=c),
        'state': 'draft',
    }


    def onchange_main_analytic_ac(self, cr, uid, ids, main_analytic, context={}):
        res = {}
        if not ids:
            return res
        iss_obj = self.browse(cr,uid,ids)
        llist = []
        if iss_obj[0].hon_line:
            for line in iss_obj[0].hon_line:
                if line.account_analytic_id:
                    llist.append((1, line.id, {'account_analytic_id': [],}))
            res = { 'value': { 'hon_line': llist },'warning': {'title': 'Let op!',
                                                               'message': 'U heeft de Titel/Nummer aangepast. '
                                                                          'Nu moet u opnieuw Redacties selecteren in de HONregel(s)'},
            }
        return res



class hon_line(orm.Model):

    _name = "hon.line"

    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        for line in self.browse(cr, uid, ids):
            price = line.price_unit * line.quantity
            res[line.id] = price
        return res

    _columns = {
        'sequence': fields.integer('Sequence', help="Gives the sequence of this line when displaying the invoice."),
        'name': fields.text('Description', required=True),
        'page_number': fields.char('Pgnr', size=64),
        'nr_of_columns': fields.float('#Cols', digits_compute= dp.get_precision('Number of Columns'), required=True),
        'hon_id': fields.many2one('hon.issue', 'Issue Reference', ondelete='cascade', select=True),
        'partner_id': fields.many2one('res.partner', 'Partner',),
        'product_category_id': fields.many2one('product.category', 'Page Type',domain=[('parent_id.supportal', '=', True)]),
        'product_id': fields.many2one('product.product', 'Product', required=True,),
        'account_id': fields.many2one('account.account', 'Account', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')],
                                      help="The income or expense account related to the selected product."),
        'uos_id': fields.many2one('product.uom', 'Unit of Measure', ondelete='set null', select=True),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
        'quantity': fields.float('Quantity', digits_compute= dp.get_precision('Product Unit of Measure'), required=True),
        'account_analytic_id': fields.many2one('account.analytic.account', string='Redactie', ),
        'company_id': fields.related('hon_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
        'price_subtotal': fields.function(_amount_line, string='Amount', type="float",
            digits_compute= dp.get_precision('Account'), store=True),
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

    def product_id_change(self, cr, uid, ids, account_analytic_id, product,  partner_id=False, price_unit=False,  context=None, company_id=None):

        if context is None:
            context = {}
        company_id = company_id if company_id != None else context.get('company_id',False)
        context = dict(context)
        context.update({'company_id': company_id, 'force_company': company_id})
        if not partner_id :
            raise osv.except_osv(_('No Partner Defined!'),_("You must first select a partner!") )
        if not product:
            raise osv.except_osv(_('No Product Defined!'),_("You must first select a Product!") )
        part = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
        if part.lang:
            context.update({'lang': part.lang})
        result = {}
        res = self.pool.get('product.product').browse(cr, uid, product, context=context)

        a = res.property_account_expense.id
        if a:
            result['account_id'] = a

        pricelist = self.pool.get('partner.product.price').search(cr, uid, [('product_id','=',product), ('partner_id','=', partner_id), ('company_id','=', company_id )], context=context)
        if not pricelist is [] :
            [price] = self.pool.get('partner.product.price').browse(cr, uid, pricelist, context=context )
            import pdb; pdb.set_trace()

            if price.price_unit:
                result.update( {'price_unit': price.price_unit} )

        aa_id_obj = self.pool.get('account.analytic.account').browse(cr, uid, account_analytic_id, context=context)
        title_id = aa_id_obj.parent_id.id

        domain = {'account_analytic_id':[('type','!=','view'),('company_id', '=', company_id),
                        ('state','not in',('close','cancelled')), ('portal_sub', '=', True),('id', 'child_of', title_id)]
        }

        res_final = {'value':result, 'domain':domain}

        return res_final

