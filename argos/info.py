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
import os

DEBUGGING = False

VERSION = '0.2.0'
REPO_NAME = "argos"
#SCRIPT_NAME = "argos"
PACKAGE_NAME = "argos"
PROJECT_NAME = "Argos"
DEFAULT_PROFILE = 'Panoptes'
SHORT_DESCRIPTION = "Argos Panoptes HDF/NCDF/scientific data viewer."
PROJECT_URL = "https://github.com/titusjan/argos"
AUTHOR = "Pepijn Kenter"
EMAIL = "titusjan@gmail.com"
ORGANIZATION_NAME = "titusjan"
ORGANIZATION_DOMAIN = "titusjan.nl"


def program_directory():
    """ Returns the program directory where this program is installed
    """
    return os.path.abspath(os.path.dirname(__file__))

def icons_directory():
    """ Returns the program directory where this program is installed
    """
    return os.path.join(program_directory(), 'img/snipicons')

