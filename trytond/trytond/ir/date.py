#This file is part of Tryton.  The COPYRIGHT file at the top level
#of this repository contains the full copyright notices and license terms.
from trytond.model import Model
import datetime


class Date(Model):
    'Date'
    _name = 'ir.date'
    _description = __doc__

    def __init__(self):
        super(Date, self).__init__()
        self._rpc.update({
            'today': False,
            })

    def today(self, cursor, user, context=None):
        '''
        Current date

        :param cursor: the database cursor
        :param user: the user id
        :param context: the context
        :return: a current datetime.date
        '''
        return datetime.date.today()

Date()
