#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

# To make a release follow these steps:
#   python setup.py sdist --formats=zip

# See also https://packaging.python.org/en/latest/distributing.html
# TODO: still can't make a wheel even following the instructions in the link below.
# http://stackoverflow.com/questions/26664102/why-can-i-not-create-a-wheel-in-pyt


if 1:
    from setuptools import setup, find_packages
else:
    print("Using distutils to import setup. No wheels enabled")
    from distutils.core import setup


from libargos import info

assert not info.DEBUGGING, "info.DEBUGGING should be False"


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

requirements = [
    # TODO: put package requirements here
]


setup(
    name = info.REPO_NAME,
    version = info.VERSION,
    description = info.SHORT_DESCRIPTION,
    long_description = readme + '\n\n' + history,
    author = info.AUTHOR,
    author_email = info.EMAIL,
    license = "GPLv3",
    url=info.PROJECT_URL,
    packages = find_packages(),
    package_data = {'': ['HISTORY.rst'], info.PACKAGE_NAME: ['img/snipicons/*']},
    scripts = ['argos'],
    install_requires = requirements,
    zip_safe = False,
    classifiers = [
        'Development Status :: 4 - Beta',
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
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development',
        'Topic :: Scientific/Engineering',
        'Topic :: Utilities',
    ],
    keywords = 'NCDF HDF plotting graphs',
    #test_suite='tests',
    #tests_require=test_requirements
)
