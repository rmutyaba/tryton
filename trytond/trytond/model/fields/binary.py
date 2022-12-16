# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from sql import Column, Null

from .field import Field
from ...transaction import Transaction
from ...tools import grouped_slice, reduce_ids
from ...filestore import filestore


class Binary(Field):
    '''
    Define a binary field (``bytes``).
    '''
    _type = 'binary'
    _sql_type = 'BLOB'
    cast = bytearray if bytes == str else bytes

    def __init__(self, string='', help='', required=False, readonly=False,
            domain=None, states=None, select=False, on_change=None,
            on_change_with=None, depends=None, context=None, loading='lazy',
            filename=None, file_id=None, store_prefix=None):
        if filename is not None:
            self.filename = filename
            if depends is None:
                depends = [filename]
            else:
                depends.append(filename)
        self.file_id = file_id
        self.store_prefix = store_prefix
        super(Binary, self).__init__(string=string, help=help,
            required=required, readonly=readonly, domain=domain, states=states,
            select=select, on_change=on_change, on_change_with=on_change_with,
            depends=depends, context=context, loading=loading)

    def get(self, ids, model, name, values=None):
        '''
        Convert the binary value into ``bytes``

        :param ids: a list of ids
        :param model: a string with the name of the model
        :param name: a string with the name of the field
        :param values: a dictionary with the read values
        :return: a dictionary with ids as key and values as value
        '''
        if values is None:
            values = {}
        transaction = Transaction()
        res = {}
        converter = self.cast
        default = None
        format_ = Transaction().context.get(
            '%s.%s' % (model.__name__, name), '')
        if format_ == 'size':
            converter = len
            default = 0

        if self.file_id:
            table = model.__table__()
            cursor = transaction.connection.cursor()

            prefix = self.store_prefix
            if prefix is None:
                prefix = transaction.database.name

            if format_ == 'size':
                store_func = filestore.size
            else:
                def store_func(id, prefix):
                    return self.cast(filestore.get(id, prefix=prefix))

            for sub_ids in grouped_slice(ids):
                cursor.execute(*table.select(
                        table.id, Column(table, self.file_id),
                        where=reduce_ids(table.id, sub_ids)
                        & (Column(table, self.file_id) != Null)
                        & (Column(table, self.file_id) != '')))
                for record_id, file_id in cursor:
                    try:
                        res[record_id] = store_func(file_id, prefix)
                    except (IOError, OSError):
                        pass

        for i in values:
            if i['id'] in res:
                continue
            value = i[name]
            if value:
                if isinstance(value, str):
                    value = value.encode('utf-8')
                value = converter(value)
            else:
                value = default
            res[i['id']] = value
        for i in ids:
            res.setdefault(i, default)
        return res

    def set(self, Model, name, ids, value, *args):
        transaction = Transaction()
        table = Model.__table__()
        cursor = transaction.connection.cursor()

        prefix = self.store_prefix
        if prefix is None:
            prefix = transaction.database.name

        args = iter((ids, value) + args)
        for ids, value in zip(args, args):
            if self.file_id:
                columns = [Column(table, self.file_id), Column(table, name)]
                values = [
                    filestore.set(value, prefix) if value else None, None]
            else:
                columns = [Column(table, name)]
                values = [self.sql_format(value)]
            cursor.execute(*table.update(columns, values,
                    where=reduce_ids(table.id, ids)))
