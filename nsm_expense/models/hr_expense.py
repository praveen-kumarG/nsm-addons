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


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

class HrExpense(models.Model):
    _inherit = 'hr.expense'


    account_id = fields.Many2one('account.account', 'Account', readonly=True,
                                 help="The partner account used for this expense.")
    state = fields.Selection(selection_add=[('revise', 'To Be Revise')])

    # Overridden:
    @api.multi
    def action_move_create(self):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        for expense in self:
            journal = expense.sheet_id.bank_journal_id if expense.payment_mode == 'company_account' else expense.sheet_id.journal_id
            #create the move that will contain the accounting entries
            acc_date = expense.sheet_id.accounting_date or expense.date
            move = self.env['account.move'].create({
                'journal_id': journal.id,
                'company_id': self.env.user.company_id.id,
                'date': acc_date,
                'ref': expense.sheet_id.name,
                # force the name to the default value, to avoid an eventual 'default_name' in the context
                # to set it to '' which cause no number to be given to the account.move when posted.
                'name': '/',
            })
            company_currency = expense.company_id.currency_id
            diff_currency_p = expense.currency_id != company_currency
            #one account.move.line per expense (+taxes..)
            move_lines = expense._move_line_get()

            #create one more move line, a counterline for the total on payable account
            payment_id = False
            total, total_currency, move_lines = expense._compute_expense_totals(company_currency, move_lines, acc_date)
            if expense.payment_mode == 'company_account':
                if not expense.sheet_id.bank_journal_id.default_credit_account_id:
                    raise UserError(_("No credit account found for the %s journal, please configure one.") % (expense.sheet_id.bank_journal_id.name))
                emp_account = expense.sheet_id.bank_journal_id.default_credit_account_id.id
                journal = expense.sheet_id.bank_journal_id
                #create payment
                payment_methods = (total < 0) and journal.outbound_payment_method_ids or journal.inbound_payment_method_ids
                journal_currency = journal.currency_id or journal.company_id.currency_id
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': total < 0 and 'outbound' or 'inbound',
                    'partner_id': expense.employee_id.address_home_id.commercial_partner_id.id,
                    'partner_type': 'supplier',
                    'journal_id': journal.id,
                    'payment_date': expense.date,
                    'state': 'reconciled',
                    'currency_id': diff_currency_p and expense.currency_id.id or journal_currency.id,
                    'amount': diff_currency_p and abs(total_currency) or abs(total),
                    'name': expense.name,
                })
                payment_id = payment.id
            else:
                if not expense.employee_id.address_home_id:
                    raise UserError(_("No Home Address found for the employee %s, please configure one.") % (expense.employee_id.name))
                emp_account = expense.employee_id.address_home_id.property_account_payable_id.id

            aml_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            move_lines.append({
                    'type': 'dest',
                    'name': aml_name,
                    'price': total,
                    'account_id': emp_account,
                    'date_maturity': acc_date,
                    'amount_currency': diff_currency_p and total_currency or False,
                    'currency_id': diff_currency_p and expense.currency_id.id or False,
                    'payment_id': payment_id,
                    })

            #convert eml into an osv-valid format
            lines = map(lambda x: (0, 0, expense._prepare_move_line(x)), move_lines)
            move.with_context(dont_create_taxes=True).write({'line_ids': lines})
            expense.sheet_id.write({'account_move_id': move.id})
            # move.post()
            if expense.payment_mode == 'company_account':
                expense.sheet_id.paid_expense_sheets()

            expense.write({'account_id': emp_account})
        return True


    @api.multi
    def write(self, vals):
        if vals.get('operating_unit_id', False):
            sheet_id = vals['sheet_id'] if vals.get('sheet_id', False) else self.sheet_id.id
            if sheet_id:
                expense_sheet = self.env['hr.expense.sheet'].browse(sheet_id)
                expense_sheet.write({'operating_unit_id':vals.get('operating_unit_id')})
        res = super(HrExpense, self).write(vals)
        return res

    @api.onchange('analytic_account_id', 'operating_unit_id')
    def anaytic_account_change(self):
        if self.analytic_account_id and self.analytic_account_id.linked_operating_unit:
            self.operating_unit_id = self.analytic_account_id.operating_unit_ids.ids[0]


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    # Overriden:
    state = fields.Selection([('submit', 'Submitted'),
                              ('post', 'Posted'),
                              ('approve', 'Approved'),
                              ('done', 'Paid'),
                              ('cancel', 'Refused'),
                              ('revise', 'To Be Revise')
                              ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False, default='submit', required=True,
        help='Expense Report State')


    @api.model
    def default_get(self, default_fields):
        res = super(HrExpenseSheet, self).default_get(default_fields) or {}
        res['journal_id'] = self.env.user.company_id.decl_journal_id.id
        return res


    #Overriden:
    @api.multi
    def approve_expense_sheets(self):
        if self.account_move_id:
            self.account_move_id.post()
        self.write({'state': 'approve', 'responsible_id': self.env.user.id})

    #Overriden:
    @api.multi
    def refuse_expenses(self, reason):
        if self.account_move_id:
            for aml in self.account_move_id.line_ids:
                if aml.reconciled:
                     raise UserError(
                         _('Please unreconcile payment accounting entries before cancelling this expense'))
            ### Then we unlink the move line
            self.account_move_id.button_cancel()
            self.account_move_id.unlink()

        self.write({'state': 'cancel'})
        for sheet in self:
            body = (_("Your Expense %s has been refused.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (sheet.name, reason))
            sheet.message_post(body=body)


    # Overriden:
    @api.multi
    def action_sheet_move_create(self):
        if any(sheet.state != 'submit' for sheet in self):
            raise UserError(_("You can only generate accounting entry for submitted expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.user.company_id.currency_id).rounding))

        res = expense_line_ids.action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and expense_line_ids:
            self.write({'state': 'post'})
        else:
            # self.write({'state': 'done'})
            self.paid_expense_sheets()
        return res


    # Overriden:
    @api.multi
    def paid_expense_sheets(self):
        if self.account_move_id:
            if not self.account_move_id.state == 'posted':
                self.account_move_id.post()

        self.write({'state': 'done'})

    @api.multi
    def revise_expense(self):
        expenses = self.expense_line_ids.filtered(lambda x: x.state == 'reported')
        self.write({'state': 'revise'})
        expenses.write({'state':'revise'})

    @api.multi
    def expense_revised(self):
        expenses = self.expense_line_ids.filtered(lambda x: x.state == 'revise')
        expenses.write({'state': 'reported'})
        self.write({'state': 'approve'})




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

