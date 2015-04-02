# -*- coding: utf-8 -*-
##################################################################################
#
# Copyright (c) 2005-2006 Axelor SARL. (http://www.axelor.com)
# and 2004-2010 Tiny SPRL (<http://tiny.be>).
#
# $Id: hr.py 4656 2006-11-24 09:58:42Z Cyp $
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import datetime
import time
from itertools import groupby
from operator import itemgetter

import math
from openerp import netsvc
from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _


class hr_holidays(osv.osv):
    _inherit = 'hr.holidays'
    
    def _get_number_of_days(self, date_from, date_to):
        """Returns a float equals to the timedelta between two dates given as string."""

        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        from_dt = datetime.datetime.strptime(date_from, DATETIME_FORMAT)
        to_dt = datetime.datetime.strptime(date_to, DATETIME_FORMAT)
#        timedelta = to_dt - from_dt
#        diff_day0 = timedelta.days + float(timedelta.seconds) / 86400
        beginnetje = datetime.date.toordinal(from_dt)
        eindje = datetime.date.toordinal(to_dt)
        verschil = eindje-beginnetje+1
        tijdlijst = []
        tijdlijst2 = []
        tijdlijst3=[]
        for i in range(verschil):
            tijdlijst.append(beginnetje+i)
        for x in range(verschil):
            tijdlijst2.append(datetime.date.fromordinal(tijdlijst[x]))
        for y in range(verschil):
            tijdlijst3.append(datetime.date.isoweekday(tijdlijst2[y]))
        zaterdagen = tijdlijst3.count(6)
        zondagen = tijdlijst3.count(7)
        weekenddagen = zaterdagen + zondagen
#        if datetime.date.isoweekday(from_dt) in(6,7) and datetime.date.isoweekday(to_dt) in(6,7):
#            diff_day = diff_day0 - weekenddagen - 1
#        else:
#            diff_day = diff_day0 - weekenddagen
        diff_day = verschil - weekenddagen
        return diff_day


    def onchange_date_from(self, cr, uid, ids, date_to, date_from):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            date_to_with_delta = datetime.datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=8)
            result['value']['date_to'] = str(date_to_with_delta)

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            #result['value']['number_of_days_temp'] = (round(math.floor(diff_day))+1)*8
            result['value']['number_of_days_temp'] = diff_day*8
        else:
            result['value']['number_of_days_temp'] = 0

        return result

    def onchange_date_to(self, cr, uid, ids, date_to, date_from):
        """
        Update the number_of_days.
        """

        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must lie before the end date.'))

        result = {'value': {}}

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            #result['value']['number_of_days_temp'] = (round(math.floor(diff_day))+1)*8
            result['value']['number_of_days_temp'] = diff_day*8
        else:
            result['value']['number_of_days_temp'] = 0

        return result