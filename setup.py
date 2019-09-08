#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

# To make a release follow these steps:
#   python setup.py sdist
#   twine upload dist/argos-0.2.0rc1.tar.gz
# or better
#   python setup.py bdist_wheel
#   twine upload dist/argos-x.y.z-py3-none-any.whl

# If you get invalid command 'bdist_wheel', you must install the 'wheel' package first.

# See also https://packaging.python.org/en/latest/distributing.html
# TODO: still can't make a wheel even following the instructions in the link below.
# http://stackoverflow.com/questions/26664102/why-can-i-not-create-a-wheel-in-pyt

import sys

def err(*args, **kwargs):
    sys.stderr.write(*args, **kwargs)
    sys.stderr.write('\n')


try:
    from setuptools import setup, find_packages
except ImportError:
    err("Argos requires setuptools for intallation. (https://pythonhosted.org/an_example_pypi_project/setuptools.html)")
    err("You can download and install it simply with: python argos/external/ez_setup.py")
    sys.exit(1)


from argos import info

if sys.version_info < (2,7) or ((3,0) <= sys.version_info < (3, 4)):
    err("Arogs requires Python 2.7 and higher or 3.4 and higher.")
    sys.exit(1)


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')


# Don't require PyQt for two reasons. First users may use PySide2 (although at the moment PySide is
# not yet working). Second, users may use Anaconda to install PyQt. Anaconda uses a different
# package name (pyqt) than pip (PyQt5) and the tools can't detect correctly if PyQt has been
# installed. This leads to trouble. See:
#   https://www.anaconda.com/using-pip-in-a-conda-environment/
#   https://github.com/ContinuumIO/anaconda-issues/issues/1554

install_requires = [
    #"PyQt5 >= 5.6.0", # Don't require PyQt. See comment above
    "cmlib",
    "numpy >= 1.11",
    # Argos will technically work without pyqtgraph and h5py, but with very limited functionality.
    # "pyqtgraph >= 0.10",
    # "h5py >= 2.6"
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
    package_data = {'': ['HISTORY.rst'], info.PACKAGE_NAME: ['img/argos.css', 'img/snipicons/*']},
    entry_points={'gui_scripts': ['argos = argos.main:main']},
    install_requires = install_requires,
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
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development',
        'Topic :: Scientific/Engineering',
        'Topic :: Utilities',
    ],
    keywords = 'NCDF HDF plotting graphs',
    #test_suite='tests',
    #tests_require=test_requirements
)
