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

import time
from lxml import etree
import openerp.addons.decimal_precision as dp
import openerp.exceptions

from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _


from openerp import models, fields as fields2, api
from openerp.exceptions import except_orm, Warning, RedirectWarning


class account_invoice(osv.osv):
    """ Inherits invoice and adds state "auth" to supplier invoice workflow """
    _inherit = 'account.invoice'

    _columns = {
        'state': fields.selection([
            ('draft','Draft'),
            ('proforma','Pro-forma'),   
            ('proforma2','Pro-forma'),
            ('open','Open'),
            ('auth','Authorized'),
            ('paid','Paid'),
            ('cancel','Cancelled'),
            ],'Status', select=True, readonly=True, track_visibility='onchange',
            help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Invoice. \
            \n* The \'Pro-forma\' when invoice is in Pro-forma status,invoice does not have an invoice number. \
            \n* The \'Authorized\' status is used when invoice is already posted, but not yet confirmed for payment. \
            \n* The \'Open\' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice. \
            \n* The \'Paid\' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled. \
            \n* The \'Cancelled\' status is used when user cancel invoice.'),
        'payment_term': fields.many2one('account.payment.term', 'Payment Terms',readonly=True, states={'draft':[('readonly',False)]},
            help="If you use payment terms, the due date will be computed automatically at the generation "\
                "of accounting entries. If you keep the payment term and the due date empty, it means direct payment. "\
                "The payment term may compute several due dates, for example 50% now, 50% in one month.",),# groups="account.group_account_invoice"),
        'user_id': fields.many2one('res.users', 'Salesperson', readonly=True, track_visibility='onchange', states={'draft':[('readonly',False)],'open':[('readonly',False)]}),
        'reference': fields.char('Invoice Reference', size=64, help="The partner reference of this invoice.",),# groups="account.group_account_invoice"),
        'amount_to_pay': fields.related('residual',
            type='float', string='Amount to be paid',
            help='The amount which should be paid at the current date.',),# groups="account.group_account_invoice"),
    }    
        
        
        
    # def action_date_assign(self, cr, uid, ids, *args):
    #     for inv in self.browse(cr, uid, ids):
    #         if not inv.date_due:
    #             res = self.onchange_payment_term_date_invoice(cr, uid, inv.id, inv.payment_term.id, inv.date_invoice)
    #             if res and res['value']:
    #                 self.write(cr, uid, [inv.id], res['value'])
    #     return True
    
    # def action_move_create(self, cr, uid, ids, context=None):
    #     """Creates invoice related analytics and financial move lines"""
    #     ait_obj = self.pool.get('account.invoice.tax')
    #     cur_obj = self.pool.get('res.currency')
    #     period_obj = self.pool.get('account.period')
    #     payment_term_obj = self.pool.get('account.payment.term')
    #     journal_obj = self.pool.get('account.journal')
    #     move_obj = self.pool.get('account.move')
    #     if context is None:
    #         context = {}
    #     for inv in self.browse(cr, uid, ids, context=context):
    #         if not inv.journal_id.sequence_id:
    #             raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
    #         if not inv.invoice_line:
    #             raise osv.except_osv(_('No Invoice Lines!'), _('Please create some invoice lines.'))
    #         if inv.move_id:
    #             continue
    #
    #         ctx = context.copy()
    #         ctx.update({'lang': inv.partner_id.lang})
    #         if not inv.date_invoice:
    #             self.write(cr, uid, [inv.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
    #         company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
    #         # create the analytical lines
    #         # one move line per invoice line
    #         iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)
    #         # check if taxes are all computed
    #         compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
    #         self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)
    #
    #         # I disabled the check_total feature
    #         group_check_total_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'group_supplier_inv_check_total')[1]
    #         group_check_total = self.pool.get('res.groups').browse(cr, uid, group_check_total_id, context=context)
    #         if group_check_total and uid in [x.id for x in group_check_total.users]:
    #             if (inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0)):
    #                 raise osv.except_osv(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))
    #
    #         if inv.payment_term:
    #             total_fixed = total_percent = 0
    #             for line in inv.payment_term.line_ids:
    #                 if line.value == 'fixed':
    #                     total_fixed += line.value_amount
    #                 if line.value == 'procent':
    #                     total_percent += line.value_amount
    #             total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
    #             if (total_fixed + total_percent) > 100:
    #                 raise osv.except_osv(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))
    #
    #         # one move line per tax line
    #         iml += ait_obj.move_line_get(cr, uid, inv.id)
    #
    #         entry_type = ''
    #         if inv.type in ('in_invoice', 'in_refund'):
    #             ref = inv.reference
    #             entry_type = 'journal_pur_voucher'
    #             if inv.type == 'in_refund':
    #                 entry_type = 'cont_voucher'
    #         else:
    #             ref = self._convert_ref(cr, uid, inv.number)
    #             entry_type = 'journal_sale_vou'
    #             if inv.type == 'out_refund':
    #                 entry_type = 'cont_voucher'
    #
    #         diff_currency_p = inv.currency_id.id <> company_currency
    #         # create one move line for the total and possibly adjust the other lines amount
    #         total = 0
    #         total_currency = 0
    #         total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml, context=ctx)
    #         acc_id = inv.account_id.id
    #
    #         name = inv['name'] or inv['supplier_invoice_number'] or '/'
    #         totlines = False
    #         if inv.payment_term:
    #             totlines = payment_term_obj.compute(cr,
    #                     uid, inv.payment_term.id, total, inv.date_invoice or False, context=ctx)
    #         if totlines:
    #             res_amount_currency = total_currency
    #             i = 0
    #             ctx.update({'date': inv.date_invoice})
    #             for t in totlines:
    #                 if inv.currency_id.id != company_currency:
    #                     amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1], context=ctx)
    #                 else:
    #                     amount_currency = False
    #
    #                 # last line add the diff
    #                 res_amount_currency -= amount_currency or 0
    #                 i += 1
    #                 if i == len(totlines):
    #                     amount_currency += res_amount_currency
    #
    #                 iml.append({
    #                     'type': 'dest',
    #                     'name': name,
    #                     'price': t[1],
    #                     'account_id': acc_id,
    #                     'date_maturity': t[0],
    #                     'amount_currency': diff_currency_p \
    #                             and amount_currency or False,
    #                     'currency_id': diff_currency_p \
    #                             and inv.currency_id.id or False,
    #                     'ref': ref,
    #                 })
    #         else:
    #             iml.append({
    #                 'type': 'dest',
    #                 'name': name,
    #                 'price': total,
    #                 'account_id': acc_id,
    #                 'date_maturity': inv.date_due or False,
    #                 'amount_currency': diff_currency_p \
    #                         and total_currency or False,
    #                 'currency_id': diff_currency_p \
    #                         and inv.currency_id.id or False,
    #                 'ref': ref
    #         })
    #
    #         date = inv.date_invoice or time.strftime('%Y-%m-%d')
    #
    #         part = self.pool.get("res.partner")._find_accounting_partner(inv.partner_id)
    #
    #         line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part.id, date, context=ctx)),iml)
    #
    #         line = self.group_lines(cr, uid, iml, line, inv)
    #
    #         journal_id = inv.journal_id.id
    #         journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
    #         if journal.centralisation:
    #             raise osv.except_osv(_('User Error!'),
    #                     _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))
    #
    #         line = self.finalize_invoice_move_lines(cr, uid, inv, line)
    #
    #         move = {
    #             'ref': inv.reference and inv.reference or inv.name,
    #             'line_id': line,
    #             'journal_id': journal_id,
    #             'date': date,
    #             'narration': inv.comment,
    #             'company_id': inv.company_id.id,
    #         }
    #         period_id = inv.period_id and inv.period_id.id or False
    #         ctx.update(company_id=inv.company_id.id,
    #                    account_period_prefer_normal=True)
    #         if not period_id:
    #             period_ids = period_obj.find(cr, uid, inv.date_invoice, context=ctx)
    #             period_id = period_ids and period_ids[0] or False
    #         if period_id:
    #             move['period_id'] = period_id
    #             for i in line:
    #                 i[2]['period_id'] = period_id
    #
    #         ctx.update(invoice=inv)
    #         move_id = move_obj.create(cr, uid, move, context=ctx)
    #         new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
    #         # make the invoice point to that move
    #         self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name}, context=ctx)
    #         # Pass invoice in context in method post: used if you want to get the same
    #         # account move reference when creating the same invoice after a cancelled one:
    #         move_obj.post(cr, uid, [move_id], context=ctx)
    #     self._log_event(cr, uid, ids)
    #     return True
    
    def invoice_validate(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'open'}, context=context)
        return True
    
#    def invoice_authorize(self, cr, uid, ids, context=None):
#        self.write(cr, uid, ids, {'state':'auth'}, context=context)
#        return True
    


# added by -- deep
class Invoice(models.Model):
    _inherit = ['account.invoice']

    @api.multi
    def action_date_assign(self):
        for inv in self:
            if not inv.date_due:
                inv._onchange_payment_term_date_invoice()
        return True


    # -- added by deep
    # no need to override the method: action_move_create
    # Invoice date is set either of Record's date or today's date

    # -- ported from Odoo 8
    @api.multi
    def move_line_id_payment_get(self):
        # return the move line ids with the same account as the invoice self
        if not self.id:
            return []
        query = """ SELECT l.id
                    FROM account_move_line l, account_invoice i
                    WHERE i.id = %s AND l.move_id = i.move_id AND l.account_id = i.account_id
                """
        self._cr.execute(query, (self.id,))
        return [row[0] for row in self._cr.fetchall()]

    # -- ported from Odoo 8
    @api.multi
    def test_paid(self):
        # check whether all corresponding account move lines are reconciled
        line_ids = self.move_line_id_payment_get()

        if not line_ids:
            return False
        query = "SELECT reconciled FROM account_move_line WHERE id IN %s"
        self._cr.execute(query, (tuple(line_ids),))
        return all(row[0] for row in self._cr.fetchall())
