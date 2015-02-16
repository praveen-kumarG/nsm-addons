# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
from datetime import datetime, timedelta
import random
from urllib import urlencode
from urlparse import urljoin

from openerp.osv import osv, fields
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from ast import literal_eval
from openerp.tools.translate import _

class res_partner(osv.Model):
    _inherit = 'res.partner'


    def _get_signup_url_for_action(self, cr, uid, ids, action='login', view_type=None, menu_id=None, res_id=None, model=None, context=None):
        """ generate a signup url for the given partner ids and action, possibly overriding 
            the url state components (menu_id, id, view_type) """
        res = dict.fromkeys(ids, False)
        base_url = self.pool.get('ir.config_parameter').get_param(cr, uid, 'web.base.url')
        for partner in self.browse(cr, uid, ids, context):
            # when required, make sure the partner has a valid signup token
            if context and context.get('signup_valid') and not partner.user_ids:
                self.signup_prepare(cr, uid, [partner.id], context=context)
                partner.refresh()

            # the parameters to encode for the query and fragment part of url
            query = {'db': cr.dbname}
            fragment = {'action': action, 'type': partner.signup_type}

            if partner.signup_token:
                fragment['token'] = partner.signup_token
            elif partner.user_ids:
                fragment['db'] = cr.dbname
                fragment['login'] = partner.user_ids[0].login
            else:
                continue        # no signup token, no user, thus no signup url!

            if view_type:
                fragment['view_type'] = view_type
            if menu_id:
                fragment['menu_id'] = menu_id
            if model:
                fragment['model'] = model
            if res_id:
                fragment['id'] = res_id

	    res[partner.id] = urljoin(base_url, "?%s&%s#%s" % (urlencode(query), urlencode(fragment), urlencode(fragment)))
        return res

    
