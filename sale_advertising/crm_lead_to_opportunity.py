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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
import re

class crm_lead2opportunity_partner(osv.osv_memory):
    _inherit = 'crm.lead2opportunity.partner'

    _columns = {
        'action': fields.selection([
            ('exist', 'Link to an existing customer'),
            ('nothing', 'Do not link to a customer')
        ], 'Related Customer', required=True),
    }

    _defaults = {
        'action': 'nothing',
    }


    def _convert_opportunity(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        lead = self.pool.get('crm.lead')
        res = False
        partner_ids_map = self._create_partner(cr, uid, ids, context=context)
        lead_ids = vals.get('lead_ids', [])
        team_id = vals.get('section_id', False)
        for lead_id in lead_ids:
            partner_id = partner_ids_map.get(lead_id, False)
            # FIXME: cannot pass user_ids as the salesman allocation only works in batch
            res = lead.convert_opportunity(cr, uid, [lead_id], partner_id, [], team_id, context=context)
        # FIXME: must perform salesman allocation in batch separately here
        user_ids = vals.get('user_ids', False)
        if user_ids:
            lead.allocate_salesman(cr, uid, lead_ids, user_ids, team_id=team_id, context=context)
        return res

    def _create_partner(self, cr, uid, ids, context=None):
        """
        Create partner based on action.
        :return dict: dictionary organized as followed: {lead_id: partner_assigned_id}
        """
        #TODO this method in only called by crm_lead2opportunity_partner
        #wizard and would probably diserve to be refactored or at least
        #moved to a better place
        if context is None:
            context = {}
        lead = self.pool.get('crm.lead')
        lead_ids = context.get('active_ids', [])
        data = self.browse(cr, uid, ids, context=context)[0]
        partner_id = data.partner_id and data.partner_id.id or False
        return lead.handle_partner_assignation(cr, uid, lead_ids, data.action, partner_id, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
