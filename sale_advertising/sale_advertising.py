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
import openerp.addons.decimal_precision as dp
import time



class sale_order(orm.Model):
    _inherit = "sale.order"


    def _amount_all(self, cr, uid, ids, name, args, context=None):
        if context is None:
            context = {}

        res = {}
        if context.get('verif_setting_change'):
            company_ids = context.get('company_ids', [])
            company_obj = self.pool['res.company'].browse(cr, uid, company_ids, context=context)
            for company in company_obj:
                treshold = company.verify_order_setting
                maxdiscount = company.verify_discount_setting
                company_id = company.id

                cr.execute("""UPDATE sale_order
                            SET ver_tr_exc=True
                            WHERE (amount_untaxed > %s
                            OR max_discount > %s)
                            AND company_id= %s
                            AND state!='paid';
                            UPDATE sale_order
                            SET ver_tr_exc=False
                            WHERE amount_untaxed <= %s
                            AND company_id= %s
                            AND max_discount <= %s
                            AND state!='paid'
                            """, ( treshold, maxdiscount, company_id,  treshold, company_id, maxdiscount ))

        else:
            cur_obj = self.pool.get('res.currency')
            res = {}
            for order in self.browse(cr, uid, ids, context=context):
                res[order.id] = {
                    'amount_untaxed': 0.0,
                    'amount_tax': 0.0,
                    'amount_total': 0.0,
                    'ver_tr_exc': None,
                }
                val = val1 = 0.0
                discount = []
                cur = order.pricelist_id.currency_id
                for line in order.order_line:
                    discount.append(line.discount)
                    val1 += line.price_subtotal
                    val += self._amount_line_tax(cr, uid, line, context=context)
                res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
                res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
                res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
                res[order.id]['max_discount'] = max(discount) or 0.0
                if order.company_id.verify_order_setting < res[order.id]['amount_untaxed'] or order.company_id.verify_discount_setting < res[order.id]['max_discount']:
                    res[order.id]['ver_tr_exc'] = True
                else:
                    res[order.id]['ver_tr_exc'] = False
        return res

    def _get_order(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('sale.order.line')
        return list(set(line['order_id'] for line in line_obj.read(
            cr, uid, ids, ['order_id'], load='_classic_write', context=context)))

    def _setting_change(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        context['company_ids'] = ids
        context['verif_setting_change'] = True
        res = ids
        return res

    _columns = {
        'published_customer': fields.many2one('res.partner', 'Published Customer'),
        'advertising_agency': fields.many2one('res.partner', 'Advertising Agency'),
        'traffic_employee': fields.many2one('res.users', 'Traffic Employee'),
        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('submitted', 'Submitted for Approval'),
            ('approved1', 'Approved by Sales Mgr'),
            ('approved2', 'Approved by Traffic'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
        ], 'Status', readonly=True, track_visibility='onchange',
            help="Gives the status of the quotation or sales order. \nThe exception status is automatically set when a "
                 "cancel operation occurs in the processing of a document linked to the sales order. \nThe 'Waiting Schedule' "
                 "status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.",
            select=True),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
                                store={'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),'sale.order.line':
                                        (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                                        },
                                multi='sums', help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
                                store={'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),'sale.order.line':
                                        (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                                        },
                                multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
                                store={'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),'sale.order.line':
                                        (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                                        },
                                multi='sums', help="The total amount."),
        'max_discount': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Max Discount',
                                store={'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),'sale.order.line':
                                        (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                                        },
                                multi='sums', help="The Maximum Discount."),
        'ver_tr_exc': fields.function(_amount_all, type="boolean", string="Verification Treshold",track_visibility='always',
                                store={'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 20), 'sale.order.line':
                                        (_get_order, ['price_unit', 'quantity', 'discount', 'product_uom_qty'], 20),'res.company':
                                        (_setting_change, ['verify_order_setting', 'verify_discount_setting'], 10),
                                        },
                                multi='all'),

    }

    def onchange_published_customer(self, cr, uid, ids, published_customer, context):
        data = {'advertising_agency':published_customer,'partner_id':published_customer, 'partner_invoice_id': False,
                'partner_shipping_id':False, 'partner_order_id':False}
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

    '''def check_order_discount(self, cr, uid, ids, context):
        data = {'partner_id':ad_agency,'partner_invoice_id': False, 'partner_shipping_id':False, 'partner_order_id':False}
        if ad_agency:
            address = self.onchange_partner_id(cr, uid, ids, ad_agency, context)
            data.update(address['value'])
        return {'value' : data}'''


class sale_advertising_issue(orm.Model):
    _name = "sale.advertising.issue"
    _inherits = {
        'account.analytic.account': 'analytic_account_id',
    }
    _description="Sale Advertising Issue"


    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'analytic_account_id': fields.many2one('account.analytic.account', required=True,
                                      string='Related Analytic Account', ondelete='restrict',
                                      help='Analytic-related data of the issue'),
        'issue_date': fields.date('Issue Date', required=True),
        'medium': fields.many2one('product.category','Medium', required=True),
        'state': fields.selection([('open','Open'),('close','Close')], 'State'),
        'default_note': fields.text('Default Note'),
    }

    # voor nsm_modules 7.0, date_publish bestaat alleen in nsm.
    def _get_issue_date(self, cr, uid, analytic_account_id, context=None):
        analytic = self.pool.get('account.analytic.account').browse(cr, uid, analytic_account_id, context=None)
        return analytic[0].date_publish

    _defaults = {
        'issue_date': _get_issue_date,
    #    'issue_date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': 'open',
    }




class sale_order_line(orm.Model):
    _inherit = "sale.order.line"


    _columns = {
        'layout_remark': fields.text('Layout Remark'),
        'adv_issue': fields.many2one('sale.advertising.issue','Advertising Issue'),
        'medium': fields.related('adv_issue', 'medium', type='many2one', relation='product.category',string='Medium', ),
        'ad_class': fields.many2one('product.category', 'Advertising Class'),
        'page_reference': fields.char('Reference of the Page', size=32),
        'from_date': fields.datetime('Start of Validity'),
        'to_date': fields.datetime('End of Validity'),
    }

    def onchange_adv_issue(self, cr, uid, ids, adv_issue=False, context=None):
        if context is None:
            context = {}
        if adv_issue:
            ad_issue = self.pool.get('sale.advertising.issue').browse(cr, uid, adv_issue, context)
            ac = ad_issue.medium and ad_issue.medium.id or False
            data = {'ad_class':
                        [('id', 'child_of', ac), ('type','!=','view')]}
            return {'domain' : data}
        return

    def onchange_ad_class(self, cr, uid, ids, ad_class=False, context=None):
        if context is None:
            context = {}
        if ad_class:
            data = {}
            template_ids = self.pool.get('product.template').search(cr, uid, [('categ_id', '=', ad_class)], context=context )
            product_ids = self.pool.get('product.product').search(cr, uid, [('product_tmpl_id', 'in', template_ids)], context=context )
            if product_ids :
                data['product_id'] = [('id', 'in', product_ids)]
                return {'domain' : data}
        return

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):

        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
            uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)

        partner = self.pool['res.partner'].browse(cr, uid, partner_id, context=context)
        discount = partner.agency_discount
        result = res['value']
        result.update({'discount': discount})
        res['value'] = result

        return res



class sale_advertising_proof(orm.Model):
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




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

