##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import os
import pathlib
from setuptools import setup, find_packages

install_requires = [
    'setuptools',
    'ZODB',
    'zope.interface',
	'bz2file'
]
extras_require = {
    'test': [
        'zope.testing',
        'manuel',
        'ZEO[test]',
    ]
}

entry_points = """
"""

# The directory containing this file
HERE = pathlib.Path(__file__).parent
# The text of the README file
README = (HERE / "README.txt").read_text()
name, version = 'src.zc.bz2storage', '1.0.11'
description="Compression improvement for ZODB",
long_description=README,
long_description_content_type="text/markdown",
url="https://github.com/qpaycm/zc.bz2storage",

setup(
    author='vir2alexport',
    author_email='vir2alexport@gmail.com',
    license='ZPL 2.1',
    name=name, version=version,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        "Framework :: Zope3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Testing",
    ],
    packages=[name.split('.')[0], name],
	namespace_packages=[name.split('.')[0]],
	package_dir={'zc.bz2storage':'zc\\bz2storage'},
    install_requires=install_requires,
    zip_safe=False,
    entry_points=entry_points,
    include_package_data=True,
    extras_require=extras_require,
	tests_require=extras_require['test'],
    test_suite=name + '.tests.test_suite',
)
