# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Magnus.nl
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

from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

class account_analytic(osv.osv):
    _inherit = 'account.analytic.account'
    

    _columns = {
        'section_id': fields.many2one('crm.case.section', 'Sales Team'),
        'department_id': fields.many2one('hr.department', 'Department'),
    }
account_analytic()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
