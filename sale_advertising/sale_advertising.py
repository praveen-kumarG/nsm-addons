# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2016 Magnus (<http://www.magnus.nl>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv, orm
import time



class sale_order(osv.osv):
    _inherit = "sale.order"

    _columns = {
        'published_customer': fields.many2one('res.partner', 'Published Customer'),
        'advertising_agency': fields.many2one('res.partner', 'Advertising Agency'),
    }

    def onchange_published_customer(self, cr, uid, ids, published_customer, context):
        data = {'advertising_agency':published_customer,'partner_id':published_customer, 'partner_invoice_id': False, 'partner_shipping_id':False, 'partner_order_id':False}
        if published_customer:
            address = self.onchange_partner_id(cr, uid, ids, published_customer, context)
            data.update(address['value'])
        return {'value' : data}

    def onchange_advertising_agency(self, cr, uid, ids, ad_agency, context):
        data = {'partner_id':ad_agency,'partner_invoice_id': False, 'partner_shipping_id':False, 'partner_order_id':False}
        if ad_agency:
            address = self.onchange_partner_id(cr, uid, ids, ad_agency, context)
            data.update(address['value'])
        return {'value' : data}

sale_order()

class sale_advertising_issue(osv.osv):
    _name = "sale.advertising.issue"
    _inherits = {
        'account.analytic.account': 'analytic_account_id',
    }
    _description="Sale Advertising Issue"


    _columns = {
        'name': fields.char('Name', size=32, required=True),
        'analytic_account_id': fields.many2one('account.analytic.account', required=True,
                                      string='Related Analytic Account', ondelete='restrict',
                                      help='Analytic-related data of the issue'),
        'issue_date': fields.date('Issue Date', required=True),
        'medium': fields.many2one('product.category','Medium', required=True),
        'state': fields.selection([('open','Open'),('close','Close')], 'State'),
        'default_note': fields.text('Default Note'),
    }

    # voor nsm_modules 7.0, date_publish bestaat alleen in nsm.
    # def _get_issue_date(self, cr, uid, analytic_account_id, context=None):
    #    analytic = self.pool.get('account.analytic.account').browse(cr, uid, analytic_account_id, context=None)
    #    return analytic[0].date_publish

    _defaults = {
    #    'issue_date': _get_issue_date,
        'issue_date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': 'open',
    }

    #def on_change_analytic(self, cr, uid, analytic_account_id, context=None):
    #    value = {}
    #    value['issue_date'] = _get_issue_date(cr, uid, analytic_account_id, context=None)

    #    return {'value': value}


sale_advertising_issue()

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"
    _columns = {
        'layout_remark': fields.text('Layout Remark'),
        'adv_issue': fields.many2one('sale.advertising.issue','Advertising Issue'),
        'ad_class': fields.many2one('product.category', 'Advertising Class'),
        'page_reference': fields.char('Reference of the Page', size=32),
        'from_date': fields.datetime('Start of Validity'),
        'to_date': fields.datetime('End of Validity'),
    }

    def onchange_adv_issue(self, cr, uid, ids, adv_issue=False, context=None):
        if context is None:
            context = {}
        if adv_issue:
            #import pdb; pdb.set_trace()
            ad_issue = self.pool.get('sale.advertising.issue').browse(cr, uid, adv_issue, context)
            ac = ad_issue.medium and ad_issue.medium.id or False
            data = {'ad_class':
                        [('id', 'child_of', ac)]}
            return {'domain' : data}
        return

    def onchange_ad_class(self, cr, uid, ids, ad_class=False, context=None):
        if context is None:
            context = {}
        if ad_class:
            data = {}
            #import pdb; pdb.set_trace()
            template_ids = self.pool.get('product.template').search(cr, uid, [('categ_id', '=', ad_class)], context=context )
            product_ids = self.pool.get('product.product').search(cr, uid, [('product_tmpl_id', 'in', template_ids)], context=context )
            if product_ids :
                data['product_id'] = [('id', 'in', product_ids)]
                return {'domain' : data}
        return

sale_order_line()

#class product_product(osv.osv):
#    _inherit = "product.product"
#    _columns = {
#        'equivalency_in_A4': fields.float('A4 Equivalency',digits=(16,2)),
#    }
#product_product()

class sale_advertising_proof(osv.osv):
    _name = "sale.advertising.proof"
    _description="Sale Advertising Proof"
    _columns = {
        'name': fields.char('Name', size=32, required=True),
        'address_id':fields.many2one('res.partner','Delivery Address', required=True),
        'number': fields.integer('Number of Copies', required=True),
        'target_id': fields.many2one('sale.order','Target', required=True),
    }
    _defaults = {
        'number': 1,
    }
sale_advertising_proof()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

