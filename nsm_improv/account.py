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
        'state': fields.selection([('draft','Unposted'), ('posted','Posted')], 'Status', required=True, readonly=True,
            help='All manually created new journal entries are usually in the status \'Unposted\', but you can set the option to skip that status on the related journal. In that case, they will behave as journal entries automatically created by the system on document validation (invoices, bank statements...) and will be created in \'Posted\' status.', track_visibility='onchange'),
    }

account_move()