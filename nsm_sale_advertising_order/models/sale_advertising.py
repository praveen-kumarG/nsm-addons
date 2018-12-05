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

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = ["sale.order"]

    material_contact_person = fields.Many2one('res.partner', 'Material Contact Person', domain=[('customer','=',True)])
    
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends('state')
    def _get_indeellijst_data(self):
        sol_pb = self.env['soline.from.odooto.pubble']
        for line in self:
            prod = line.product_id
            if prod:
                line.product_width = prod.width
                line.product_height = prod.height
            pubbleObj = sol_pb.search([('odoo_order_line', '=', line.id)])
            if pubbleObj:
                line.mapping_remark = pubbleObj[0].ad_productiondetail_placementcomments
                line.material_id = pubbleObj[0].ad_materialid


    @api.depends('proof_number_payer','proof_number_adv_customer')
    def _get_proof_data(self):
        for line in self:
            proof_payer = line.proof_number_payer
            proof_cus = line.proof_number_adv_customer and line.proof_number_adv_customer[0]
            if proof_payer:
                line.proof_parent_name = proof_payer.parent_id and proof_payer.parent_id.name or False
                line.proof_initials = proof_payer.initials or ''
                line.proof_infix = proof_payer.infix or ''
                line.proof_lastname = proof_payer.lastname or ''
                line.proof_country_code = proof_payer.country_id.code or ''
                line.proof_zip = proof_payer.zip or ''
                line.proof_street_number = proof_payer.street_number or ''
                line.proof_street_name = proof_payer.street_name or ''
                line.proof_city = proof_payer.city or ''
                line.proof_partner_name = proof_payer.name or ''
            elif proof_cus:
                line.proof_parent_name = proof_cus.parent_id and proof_cus.parent_id.name or False
                line.proof_initials = proof_cus.initials or ''
                line.proof_infix = proof_cus.infix or ''
                line.proof_lastname = proof_cus.lastname or ''
                line.proof_country_code = proof_cus.country_id.code or ''
                line.proof_zip = proof_cus.zip or ''
                line.proof_street_number = proof_cus.street_number or ''
                line.proof_street_name = proof_cus.street_name or ''
                line.proof_city = proof_cus.city or ''
                line.proof_partner_name = proof_cus.name or ''

    @api.model
    def default_get(self, fields_list):
        result = super(SaleOrderLine, self).default_get(fields_list)
        if 'customer_contact' in self.env.context:
            result.update({'proof_number_payer':self.env.context['customer_contact']})
        return result

    @api.onchange('ad_class', 'title', 'title_ids')
    def onchange_ad_clsss_title(self):
        vals, data, result = {}, {}, {}
        vals['product_template_id'] = False
        data['product_template_id'] = []
        if self.ad_class: data['product_template_id'] += [('categ_id', '=', self.ad_class.id)]
        titles = self.title if self.title else self.title_ids or False
        if titles:
            product_ids = self.env['product.product']
            for title in titles:
                if title.product_attribute_value_id:
                    product_ids = product_ids.search([('attribute_value_ids', '=', [title.product_attribute_value_id.id])])
                    product_ids += product_ids

            if product_ids:
                product_tmpl_ids = product_ids.mapped('product_tmpl_id').ids
                data['product_template_id'] += [('id', 'in', product_tmpl_ids)]
        return {'value': vals, 'domain': data, 'warning': result}

    proof_number_payer = fields.Many2one('res.partner', 'Proof Number Payer')
    proof_number_adv_customer = fields.Many2many('res.partner', 'partner_line_proof_rel', 'line_id', 'partner_id', string='Proof Number Advertising Customer')
    proof_number_amt_payer = fields.Integer('Proof Number Amount Payer', default=1)
    proof_number_amt_adv_customer = fields.Integer('Proof Number Amount Advertising', default=1)
    proof_parent_name = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Parent")
    proof_initials = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Initials")
    proof_infix = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Infix")
    proof_lastname = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Last Name")
    proof_country_code = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Country Code")
    proof_zip = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Zip")
    proof_street_number = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Street Number")
    proof_street_name = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Street Name")
    proof_city = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="City")
    proof_partner_name = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Name")
    product_width = fields.Float(compute='_get_indeellijst_data', readonly=True, store=False, string="Width")
    product_height = fields.Float(compute='_get_indeellijst_data', readonly=True, store=False, string="Height")
    mapping_remark = fields.Char(compute='_get_indeellijst_data', readonly=True, store=False, string="Mapping Remark")
    material_id = fields.Integer(compute='_get_indeellijst_data', readonly=True, store=False, string="Material ID")


