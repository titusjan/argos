# -*- coding: utf-8 -*-

# This file is part of Argos.
#
# Argos is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Argos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Argos. If not, see <http://www.gnu.org/licenses/>.

""" Version and other info for this program
"""
import os, sys

# We bypass the argparse mechanism in main.py because this import is executed before main.main()
DEBUGGING = ('-d' in sys.argv or '--debug' in sys.argv)
TESTING = True # add some test menu options
PROFILING = False# and DEBUGGING

VERSION = '0.4.2'
REPO_NAME = "argos"
SCRIPT_NAME = "argos"
PACKAGE_NAME = "argos"
PROJECT_NAME = "Argos"
SHORT_DESCRIPTION = "Argos HDF5/NetCDF/scientific data viewer."
PROJECT_URL = "https://github.com/titusjan/argos"
AUTHOR = "Pepijn Kenter"
EMAIL = "titusjan@gmail.com"
ORGANIZATION_NAME = "titusjan"
ORGANIZATION_DOMAIN = "titusjan.nl"

EXIT_CODE_SUCCESS = 0
EXIT_CODE_ERROR = 1
EXIT_CODE_COMMAND_ARGS = 2
EXIT_CODE_RESTART = 66 # Indicates the program is being 'restarted'

KEY_PROGRAM = '_program'
KEY_VERSION = '_version'

# TODO: move to utils locations
def program_directory():
    """ Returns the program directory where this program is installed
    """
    return os.path.abspath(os.path.dirname(__file__))


def resource_directory():
    """ Returns directory with resources (images, style sheets, etc)
    """
    return os.path.join(program_directory(), 'img/')



def icons_directory():
    """ Returns the icons directory
    """
    return os.path.join(program_directory(), 'img/snipicons')

