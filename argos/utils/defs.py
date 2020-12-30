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


""" Various definitions, errors and constants that can be used throughout the program

"""
import sys

CONTIGUOUS = 'contiguous'  # contiguous chunking

# String formatting template for numbered dimension names
DIM_TEMPLATE = "dim-{}"
SUB_DIM_TEMPLATE = "subdim-{}"

# Use different unicode character per platform as it looks better.
if sys.platform == 'linux':
    RIGHT_ARROW = "\u2794"
elif sys.platform == 'win32' or sys.platform == 'cygwin':
    RIGHT_ARROW = "\u2794"
elif sys.platform == 'darwin':
    RIGHT_ARROW = "\u279E"
else:
    RIGHT_ARROW = "\u2794"


class InvalidInputError(Exception):
    """ Exception raised when the input is invalid after editing
    """
    pass
