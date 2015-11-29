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


from openerp.osv import fields, osv, expression


class account_move(osv.osv):

    _name = "account.move"
#    _inherit =
    _inherit = ['account.move','mail.thread']

    _track = {
        'state': {
        }
    }
    _columns = {
#        'name': fields.char('Number', size=64, required=True),
#        'ref': fields.char('Reference', size=64),
#        'period_id': fields.many2one('account.period', 'Period', required=True, states={'posted':[('readonly',True)]}),
#        'journal_id': fields.many2one('account.journal', 'Journal', required=True, states={'posted':[('readonly',True)]}),
        'state': fields.selection([('draft','Unposted'), ('posted','Posted')], 'Status', required=True, readonly=True,
            help='All manually created new journal entries are usually in the status \'Unposted\', but you can set the option to skip that status on the related journal. In that case, they will behave as journal entries automatically created by the system on document validation (invoices, bank statements...) and will be created in \'Posted\' status.', track_visibility='always'),
#        'line_id': fields.one2many('account.move.line', 'move_id', 'Entries', states={'posted':[('readonly',True)]}),
#        'to_check': fields.boolean('To Review', help='Check this box if you are unsure of that journal entry and if you want to note it as \'to be reviewed\' by an accounting expert.'),
#        'partner_id': fields.related('line_id', 'partner_id', type="many2one", relation="res.partner", string="Partner", store={
#            _name: (lambda self, cr,uid,ids,c: ids, ['line_id'], 10),
#            'account.move.line': (_get_move_from_lines, ['partner_id'],10)
#            }),
#        'amount': fields.function(_amount_compute, string='Amount', digits_compute=dp.get_precision('Account'), type='float', fnct_search=_search_amount),
#        'date': fields.date('Date', required=True, states={'posted':[('readonly',True)]}, select=True),
#        'narration':fields.text('Internal Note'),
#        'company_id': fields.related('journal_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
#        'balance': fields.float('balance', digits_compute=dp.get_precision('Account'), help="This is a field only used for internal purpose and shouldn't be displayed"),
    }

#    _defaults = {
#        'name': '/',
#        'state': 'draft',
#        'period_id': _get_period,
#        'date': fields.date.context_today,
#        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
#    }
account_move()