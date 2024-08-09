# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import os

from trytond.tests.test_tryton import TEST_NETWORK, load_doc_tests


def load_tests(*args, **kwargs):
    if (not TEST_NETWORK
            or not (os.getenv('MYGLS_USERNAME')
                and os.getenv('MYGLS_PASSWORD')
                and os.getenv('MYGLS_CLIENT_NUMBER'))):
        kwargs.setdefault('skips', set()).add(
                'scenario_stock_package_shipping_mygls.rst')
    return load_doc_tests(__name__, __file__, *args, **kwargs)
