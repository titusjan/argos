#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from libargos import info
from libargos.qt import USE_PYQT

assert not info.DEBUGGING, "info.DEBUGGING should be False" 
assert USE_PYQT, "USE_PYQT should be True"


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
        info.PACKAGE_NAME, entry points
    ],
    package_dir={info.PACKAGE_NAME: info.PACKAGE_NAME},
    scripts = ['argos'], 
    include_package_data=True,
    install_requires=requirements,
    license="GPLv3",
    zip_safe=False,
    keywords='NCDF HDF plotting graphs',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Developers', 
        'Intended Audience :: End Users/Desktop', 
        'Intended Audience :: Science/Research', 
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development',
        'Topic :: Scientific/Engineering',
        'Topic :: Utilities',
    ],
    test_suite='tests',
    tests_require=test_requirements
)