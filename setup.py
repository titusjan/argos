#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from libemptyqt import info

assert not info.DEBUGGING, "info.DEBUGGING should be False" 


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name=info.REPO_NAME,
    version=info.VERSION,
    description=info.SHORT_DESCRIPTION,
    long_description=readme + '\n\n' + history,
    author=info.AUTOR,
    author_email=info.EMAIL,
    url=info.PROJECT_URL,
    packages=[
        info.PACKAGE_NAME,
    ],
    package_dir={info.PACKAGE_NAME: info.PACKAGE_NAME},
    include_package_data=True,
    install_requires=requirements,
    license="GPLv3",
    zip_safe=False,
    keywords='space separated keywords',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements
)