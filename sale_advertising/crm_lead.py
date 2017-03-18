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
from openerp.tools.translate import _

class crm_lead(orm.Model):
    _inherit = "crm.lead"
    _columns = {
        'published_customer': fields.many2one('res.partner', 'Advertiser', domain=[('customer', '=', True)], ondelete='set null',
                                              track_visibility='onchange',
                                        select=True,
                                        help="Linked Advertiser (optional). "),
        'partner_id': fields.many2one('res.partner', 'Payer', ondelete='set null', track_visibility='onchange',
                                        select=True,
                                        help="Linked Payer (optional)."),
        'partner_invoice_id': fields.many2one('res.partner', 'Payer Invoice Address', ondelete='set null',
                                      select=True,
                                      help="Linked partner (optional). Usually created when converting the lead."),
        'partner_contact_id': fields.many2one('res.partner', 'Contact Person', ondelete='set null', track_visibility='onchange',
                                        select=True,
                                        help="Linked Contact Person (optional). Usually created when converting the lead."),
        'ad_agency_id': fields.many2one('res.partner', 'Agency', ondelete='set null', track_visibility='onchange',
                                      select=True,
                                      help="Linked Advertising Agency (optional). Usually created when converting the lead."),
        'partner_acc_mgr': fields.related('partner_id', 'user_id', type='many2one', relation='res.users',
                                          string='Account Manager', store=True),

    }

    def onchange_published_customer(self, cr, uid, ids, published_customer, context):
        if published_customer:
            advertiser = self.pool.get('res.partner').browse(cr, uid, published_customer, context=context)
            values = {
                'partner_name': advertiser.name,
                'partner_id': published_customer,
                'title': advertiser.title and advertiser.title.id or False,
                'email_from': advertiser.email,
                'phone': advertiser.phone,
                'mobile': advertiser.mobile,
                'fax': advertiser.fax,
                'zip': advertiser.zip,
                'function': advertiser.function,
                'ad_agency_id': False,
            }
        return {'value' : values }

    def onchange_agency(self, cr, uid, ids, ad_agency, context):
        values = {}
        if ad_agency:
            agency = self.pool.get('res.partner').browse(cr, uid, ad_agency, context=context)
            values = {
                'partner_id': ad_agency,
                'title': agency.title and agency.title.id or False,
                'email_from': agency.email,
                'phone': agency.phone,
                'mobile': agency.mobile,
                'fax': agency.fax,
                'zip': agency.zip,
                'function': agency.function,
            }
        return {'value' : values}

    def onchange_partner(self, cr, uid, ids, part, context=None):
        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
        values = {}

        if part.type == 'contact':
            contact = self.pool['res.partner'].search(cr, uid, [('is_company','=', False),('type','=', 'contact'),('parent_id','=', part.id)], context=context)
            if len(contact) >=1:
                contact_id = contact[0]
            else:
                contact_id = False
        elif addr['contact'] == addr['default']:
            contact_id = False
        else: contact_id = addr['contact']
        invoice = self.pool.get('res.partner').browse(cr, uid, addr['invoice'], context=context)

        values = {
            'street': invoice.street,
            'street2': invoice.street2,
            'city': invoice.city,
            'state_id': invoice.state_id and invoice.state_id.id or False,
            'country_id': invoice.country_id and invoice.country_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_contact_id': contact_id,
        }
        return {'value' : values}


    def onchange_contact(self, cr, uid, ids, partner_id, context=None):
        values = {}
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            values = {
                'contact_name': partner.name,
                'title': partner.title and partner.title.id or False,
                'email_from' : partner.email,
                'phone' : partner.phone,
                'mobile' : partner.mobile,
                'fax' : partner.fax,
                'function': partner.function,
            }
        else:
            values['contact_name'] = False
        return {'value' : values}

    def _convert_opportunity_data(self, cr, uid, lead, customer, section_id=False, context=None):
        crm_stage = self.pool.get('crm.case.stage')
        contact_id = False
        if customer:
            contact_id = self.pool.get('res.partner').address_get(cr, uid, [customer.id])['default']
        if not section_id:
            section_id = lead.section_id and lead.section_id.id or False
        val = {
            'planned_revenue': lead.planned_revenue,
            'probability': lead.probability,
            'name': lead.name,
            'partner_id': customer and customer.id or False,
            'user_id': (lead.user_id and lead.user_id.id),
            'type': 'opportunity',
            'date_action': fields.datetime.now(),
            'date_open': fields.datetime.now(),
            'email_from': customer and customer.email or lead.email_from,
            'phone': customer and customer.phone or lead.phone,
        }
        if not lead.stage_id or lead.stage_id.type=='lead':
            val['stage_id'] = self.stage_find(cr, uid, [lead], section_id, [('state', '=', 'draft'),('type', 'in', ('opportunity','both'))], context=context)
        return val

    def convert_opportunity(self, cr, uid, ids, partner_id, user_ids=False, section_id=False, context=None):
        customer = False
        if partner_id:
            partner = self.pool.get('res.partner')
            customer = partner.browse(cr, uid, partner_id, context=context)
        for lead in self.browse(cr, uid, ids, context=context):
            if lead.state in ('done', 'cancel'):
                continue
            vals = self._convert_opportunity_data(cr, uid, lead, customer, section_id, context=context)
            self.write(cr, uid, [lead.id], vals, context=context)
        self.message_post(cr, uid, ids, body=_("Lead <b>converted into an Opportunity</b>"), subtype="crm.mt_lead_convert_to_opportunity", context=context)

        if user_ids or section_id:
            self.allocate_salesman(cr, uid, ids, user_ids, section_id, context=context)

        return True

    def handle_partner_assignation(self, cr, uid, ids, action='create', partner_id=False, context=None):
        """
        Handle partner assignation during a lead conversion.
        if action is 'create', create new partner with contact and assign lead to new partner_id.
        otherwise assign lead to the specified partner_id

        :param list ids: leads/opportunities ids to process
        :param string action: what has to be done regarding partners (create it, assign an existing one, or nothing)
        :param int partner_id: partner to assign if any
        :return dict: dictionary organized as followed: {lead_id: partner_assigned_id}
        """
        #TODO this is a duplication of the handle_partner_assignation method of crm_phonecall
        partner_ids = {}
        # If a partner_id is given, force this partner for all elements
        force_partner_id = partner_id
        for lead in self.browse(cr, uid, ids, context=context):
            # If the action is set to 'create' and no partner_id is set, create a new one
            if action == 'create':
                partner_id = force_partner_id or self._create_lead_partner(cr, uid, lead, context)
            self._lead_set_partner(cr, uid, lead, partner_id, context=context)
            partner_ids[lead.id] = partner_id
        return partner_ids

    def allocate_salesman(self, cr, uid, ids, user_ids=None, team_id=False, context=None):
        """
        Assign salesmen and salesteam to a batch of leads.  If there are more
        leads than salesmen, these salesmen will be assigned in round-robin.
        E.g.: 4 salesmen (S1, S2, S3, S4) for 6 leads (L1, L2, ... L6).  They
        will be assigned as followed: L1 - S1, L2 - S2, L3 - S3, L4 - S4,
        L5 - S1, L6 - S2.

        :param list ids: leads/opportunities ids to process
        :param list user_ids: salesmen to assign
        :param int team_id: salesteam to assign
        :return bool
        """
        index = 0

        for lead_id in ids:
            value = {}
            if team_id:
                value['section_id'] = team_id
            if user_ids:
                value['user_id'] = user_ids[index]
                # Cycle through user_ids
                index = (index + 1) % len(user_ids)
            if value:
                self.write(cr, uid, [lead_id], value, context=context)
        return True



class crm_make_sale(osv.osv_memory):
    """ Make sale  order for crm """
    _inherit = "crm.make.sale"

    def makeOrder(self, cr, uid, ids, context=None):
        """
        This function  create Quotation on given case.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of crm make sales' ids
        @param context: A standard dictionary for contextual values
        @return: Dictionary value of created sales order.

        Override from sale_crm.crm_make_sale, in which user_id is not
        taken from partner, but just uid.
        """
        if context is None:
            context = {}
        # update context: if come from phonecall, default state values can make the quote crash lp:1017353
        context.pop('default_state', False)

        case_obj = self.pool.get('crm.lead')
        sale_obj = self.pool.get('sale.order')
        partner_obj = self.pool.get('res.partner')
        data = context and context.get('active_ids', []) or []

        for make in self.browse(cr, uid, ids, context=context):
            partner = make.partner_id
            partner_addr = partner_obj.address_get(cr, uid, [partner.id],
                                                   ['default', 'invoice', 'delivery', 'contact'])
            pricelist = partner.property_product_pricelist.id
            fpos = partner.property_account_position and partner.property_account_position.id or False
            payment_term = partner.property_payment_term and partner.property_payment_term.id or False
            new_ids = []
            for case in case_obj.browse(cr, uid, data, context=context):
                if not partner and case.partner_id:
                    partner = case.partner_id
                    fpos = partner.property_account_position and partner.property_account_position.id or False
                    payment_term = partner.property_payment_term and partner.property_payment_term.id or False
                    partner_addr = partner_obj.address_get(cr, uid, [partner.id],
                                                           ['default', 'invoice', 'delivery', 'contact'])
                    pricelist = partner.property_product_pricelist.id
                if False in partner_addr.values():
                    raise osv.except_osv(_('Insufficient Data!'), _('No address(es) defined for this customer.'))

                vals = {
                    'origin': _('Opportunity: %s') % str(case.id),
                    'section_id': case.section_id and case.section_id.id or False,
                    'categ_ids': [(6, 0, [categ_id.id for categ_id in case.categ_ids])],
                    'shop_id': make.shop_id.id,
                    'partner_id': partner.id,
                    'pricelist_id': pricelist,
                    'partner_invoice_id': partner_addr['invoice'],
                    'partner_shipping_id': partner_addr['delivery'],
                    'date_order': fields.date.context_today(self, cr, uid, context=context),
                    'fiscal_position': fpos,
                    'payment_term': payment_term,
                    'user_id': uid,
                    'opportunity_subject': case.name,
                }
                new_id = sale_obj.create(cr, uid, vals, context=context)
                sale_order = sale_obj.browse(cr, uid, new_id, context=context)
                case_obj.write(cr, uid, [case.id], {'ref': 'sale.order,%s' % new_id})
                new_ids.append(new_id)
                message = _("Opportunity has been <b>converted</b> to the quotation <em>%s</em>.") % (sale_order.name)
                case.message_post(body=message)
            if make.close:
                case_obj.case_close(cr, uid, data)
            if not new_ids:
                return {'type': 'ir.actions.act_window_close'}
            if len(new_ids) <= 1:
                value = {
                    'domain': str([('id', 'in', new_ids)]),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sale.order',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Quotation'),
                    'res_id': new_ids and new_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', new_ids)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'sale.order',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Quotation'),
                    'res_id': new_ids
                }
            return value




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

