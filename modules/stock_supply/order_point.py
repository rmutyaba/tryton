# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from sql import Null

from trytond.i18n import gettext
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Equal, Eval, If, In, Not
from trytond.transaction import Transaction

from .exceptions import OrderPointValidationError


class OrderPoint(ModelSQL, ModelView):
    """
    Order Point
    Provide a way to define a supply policy for each
    product on each locations. Order points on warehouse are
    considered by the supply scheduler to generate purchase requests.
    """
    __name__ = 'stock.order_point'
    product = fields.Many2One(
        'product.product', "Product", required=True,
        domain=[
            ('type', '=', 'goods'),
            ('consumable', '=', False),
            ('purchasable', 'in', If(Equal(Eval('type'), 'purchase'),
                    [True], [True, False])),
            ],
        context={
            'company': Eval('company', -1),
            },
        depends={'company'})
    location = fields.Many2One(
        'stock.location', "Location", required=True,
        domain=[
            If(Eval('type') == 'internal',
                ('type', '=', 'storage'),
                ('type', '=', 'warehouse')),
            ])
    provisioning_location = fields.Many2One(
        'stock.location', 'Provisioning Location',
        domain=[('type', 'in', ['storage', 'view'])],
        states={
            'invisible': Not(Equal(Eval('type'), 'internal')),
            'required': ((Eval('type') == 'internal')
                & (Eval('min_quantity', None) != None)),  # noqa: E711
        })
    overflowing_location = fields.Many2One(
        'stock.location', 'Overflowing Location',
        domain=[('type', 'in', ['storage', 'view'])],
        states={
            'invisible': Eval('type') != 'internal',
            'required': ((Eval('type') == 'internal')
                & (Eval('max_quantity', None) != None)),  # noqa: E711
            })
    type = fields.Selection(
        [('internal', 'Internal'),
         ('purchase', 'Purchase')],
        "Type", required=True)
    min_quantity = fields.Float(
        "Minimal Quantity", digits='unit',
        states={
            # required for purchase and production types
            'required': Eval('type') != 'internal',
            },
        domain=['OR',
            ('min_quantity', '=', None),
            ('min_quantity', '<=', Eval('target_quantity', 0)),
            ])
    target_quantity = fields.Float(
        "Target Quantity", digits='unit', required=True,
        domain=[
            ['OR',
                ('min_quantity', '=', None),
                ('target_quantity', '>=', Eval('min_quantity', 0)),
                ],
            ['OR',
                ('max_quantity', '=', None),
                ('target_quantity', '<=', Eval('max_quantity', 0)),
                ],
            ])
    max_quantity = fields.Float(
        "Maximal Quantity", digits='unit',
        states={
            'invisible': Eval('type') != 'internal',
            },
        domain=['OR',
            ('max_quantity', '=', None),
            ('max_quantity', '>=', Eval('target_quantity', 0)),
            ])
    company = fields.Many2One('company.company', 'Company', required=True)
    unit = fields.Function(fields.Many2One('product.uom', 'Unit'), 'get_unit')

    @classmethod
    def __register__(cls, module):
        table = cls.__table__()
        table_h = cls.__table_handler__(module)
        cursor = Transaction().connection.cursor()

        super().__register__(module)

        # Migration from 7.2: merge warehouse_location and storage_location
        if table_h.column_exist('warehouse_location'):
            cursor.execute(*table.update(
                    [table.location],
                    [table.warehouse_location],
                    where=(table.location == Null)
                    & (table.warehouse_location != Null)))
            table_h.drop_column('warehouse_location')
        if table_h.column_exist('storage_location'):
            cursor.execute(*table.update(
                    [table.location],
                    [table.storage_location],
                    where=(table.location == Null)
                    & (table.storage_location != Null)))
            table_h.drop_column('storage_location')

    @staticmethod
    def default_type():
        return "purchase"

    @fields.depends('type', 'location')
    def on_change_type(self):
        if self.type == 'internal' and self.location:
            if self.location.type != 'storage':
                self.location = None
        elif self.location:
            if self.location.type != 'warehouse':
                self.location = None

    @classmethod
    def default_location(cls):
        return Pool().get('stock.location').get_default_warehouse()

    @fields.depends('product', '_parent_product.default_uom')
    def on_change_product(self):
        self.unit = None
        if self.product:
            self.unit = self.product.default_uom

    def get_unit(self, name):
        return self.product.default_uom.id

    @classmethod
    def validate(cls, orderpoints):
        super(OrderPoint, cls).validate(orderpoints)
        cls.check_concurrent_internal(orderpoints)
        cls.check_uniqueness(orderpoints)

    @classmethod
    def check_concurrent_internal(cls, orders):
        """
        Ensure that there is no 'concurrent' internal order
        points. I.E. no two order point with opposite location for the
        same product and same company.
        """
        internals = cls.browse([o for o in orders if o.type == 'internal'])
        if not internals:
            return

        for location_name in [
                'provisioning_location', 'overflowing_location']:
            query = []
            for op in internals:
                if getattr(op, location_name, None) is None:
                    continue
                arg = ['AND',
                    ('product', '=', op.product.id),
                    (location_name, '=', op.location.id),
                    ('location', '=',
                        getattr(op, location_name).id),
                    ('company', '=', op.company.id),
                    ('type', '=', 'internal')]
                query.append(arg)
            if query and cls.search(['OR'] + query):
                raise OrderPointValidationError(
                    gettext('stock_supply'
                        '.msg_order_point_concurrent_%s_internal' %
                        location_name))

    @staticmethod
    def _type2field(type=None):
        t2f = {
            'purchase': 'location',
            'internal': 'location',
            }
        if type is None:
            return t2f
        else:
            return t2f[type]

    @classmethod
    def check_uniqueness(cls, orders):
        """
        Ensure uniqueness of order points. I.E that there is no several
        order point for the same location, the same product and the
        same company.
        """
        query = ['OR']
        for op in orders:
            field = cls._type2field(op.type)
            arg = ['AND',
                ('product', '=', op.product.id),
                (field, '=', getattr(op, field).id),
                ('id', '!=', op.id),
                ('company', '=', op.company.id),
                ]
            query.append(arg)
        if cls.search(query):
            raise OrderPointValidationError(
                gettext('stock_supply.msg_order_point_unique'))

    @property
    def warehouse_location(self):
        if self.type == 'purchase':
            return self.location

    @property
    def storage_location(self):
        if self.type == 'internal':
            return self.location

    def get_rec_name(self, name):
        return "%s @ %s" % (self.product.name, self.location.name)

    @classmethod
    def search_rec_name(cls, name, clause):
        _, operator, value = clause
        if operator.startswith('!') or operator.startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op,
            ('location.rec_name', *clause[1:]),
            ('product.rec_name', *clause[1:]),
            ]

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @classmethod
    def supply_stock(cls):
        pool = Pool()
        StockSupply = pool.get('stock.supply', type='wizard')
        session_id, _, _ = StockSupply.create()
        StockSupply.execute(session_id, {}, 'create_')
        StockSupply.delete(session_id)
