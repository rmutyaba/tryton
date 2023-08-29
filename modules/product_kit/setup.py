#!/usr/bin/env python3
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import io
import os
import re
from configparser import ConfigParser

from setuptools import find_packages, setup


def read(fname):
    content = io.open(
        os.path.join(os.path.dirname(__file__), fname),
        'r', encoding='utf-8').read()
    content = re.sub(
        r'(?m)^\.\. toctree::\r?\n((^$|^\s.*$)\r?\n)*', '', content)
    return content


def get_require_version(name):
    require = '%s >= %s.%s, < %s.%s'
    require %= (name, major_version, minor_version,
        major_version, minor_version + 1)
    return require


config = ConfigParser()
config.read_file(open(os.path.join(os.path.dirname(__file__), 'tryton.cfg')))
info = dict(config.items('tryton'))
for key in ('depends', 'extras_depend', 'xml'):
    if key in info:
        info[key] = info[key].strip().splitlines()
version = info.get('version', '0.0.1')
major_version, minor_version, _ = version.split('.', 2)
major_version = int(major_version)
minor_version = int(minor_version)
name = 'trytond_product_kit'

if minor_version % 2:
    download_url = ''
else:
    download_url = 'http://downloads.tryton.org/%s.%s/' % (
        major_version, minor_version)

requires = []
for dep in info.get('depends', []):
    if not re.match(r'(ir|res)(\W|$)', dep):
        requires.append(get_require_version('trytond_%s' % dep))
requires.append(get_require_version('trytond'))

tests_require = [
    get_require_version('proteus'),
    get_require_version('trytond_account_invoice'),
    get_require_version('trytond_account_invoice_stock'),
    get_require_version('trytond_company'),
    get_require_version('trytond_purchase'),
    get_require_version('trytond_purchase_amendment'),
    get_require_version('trytond_sale'),
    get_require_version('trytond_sale_amendment'),
    get_require_version('trytond_stock'),
    ]

setup(name=name,
    version=version,
    description='Tryton module to manage product kits and components',
    long_description=read('README.rst'),
    author='Tryton',
    author_email='foundation@tryton.org',
    url='http://www.tryton.org/',
    download_url=download_url,
    project_urls={
        "Bug Tracker": 'https://bugs.tryton.org/',
        "Documentation": ('https://docs.tryton.org/projects/'
            'modules-product-kit'),
        "Forum": 'https://www.tryton.org/forum',
        "Source Code": 'https://code.tryton.org/tryton',
        },
    keywords='',
    package_dir={'trytond.modules.product_kit': '.'},
    packages=(
        ['trytond.modules.product_kit']
        + ['trytond.modules.product_kit.%s' % p
            for p in find_packages()]
        ),
    package_data={
        'trytond.modules.product_kit': (info.get('xml', [])
            + ['tryton.cfg', 'view/*.xml', 'locale/*.po', '*.fodt',
                'icons/*.svg', 'tests/*.rst']),
        },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Plugins',
        'Framework :: Tryton',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Legal Industry',
        'License :: OSI Approved :: '
        'GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: Bulgarian',
        'Natural Language :: Catalan',
        'Natural Language :: Chinese (Simplified)',
        'Natural Language :: Czech',
        'Natural Language :: Dutch',
        'Natural Language :: English',
        'Natural Language :: Finnish',
        'Natural Language :: French',
        'Natural Language :: German',
        'Natural Language :: Hungarian',
        'Natural Language :: Indonesian',
        'Natural Language :: Italian',
        'Natural Language :: Persian',
        'Natural Language :: Polish',
        'Natural Language :: Portuguese (Brazilian)',
        'Natural Language :: Romanian',
        'Natural Language :: Russian',
        'Natural Language :: Slovenian',
        'Natural Language :: Spanish',
        'Natural Language :: Turkish',
        'Natural Language :: Ukrainian',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Office/Business',
        ],
    license='GPL-3',
    python_requires='>=3.8',
    install_requires=requires,
    extras_require={
        'test': tests_require,
        },
    zip_safe=False,
    entry_points="""
    [trytond.modules]
    product_kit = trytond.modules.product_kit
    """,  # noqa: E501
    )
