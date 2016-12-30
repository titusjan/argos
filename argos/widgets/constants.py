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

""" Constants related to the layout and other widget properties.
"""
import sys
from argos.qt import QtCore

#TREE_ROW_HEIGHT = 20 # pixels
TREE_CELL_SIZE_HINT = QtCore.QSize(100, 20)
TREE_ICON_SIZE = QtCore.QSize(16, 16)

#COLLECTOR_TREE_CELL_SIZE_HINT = QtCore.QSize(100, 24) not used (yet?)
COLLECTOR_TREE_ICON_SIZE = QtCore.QSize(20, 20)

# Initial dock widths of the main window
LEFT_DOCK_WIDTH = 350
RIGHT_DOCK_WIDTH = 320
TOP_DOCK_HEIGHT = 75

COL_NODE_NAME_WIDTH = 170
COL_SHAPE_WIDTH = 60
COL_ELEM_TYPE_WIDTH = 60


# Spacing and margin in central widgets in pixels
CENTRAL_SPACING = 0
CENTRAL_MARGIN  = 0

# Spacing and margin in dock widgets in pixels
if sys.platform == 'darwin': # OS-X
    DOCK_SPACING = 10
    DOCK_MARGIN  = 10
else:
    DOCK_SPACING = 5
    DOCK_MARGIN  = 5


if sys.platform == 'linux':
    MONO_FONT = 'Monospace'
    FONT_SIZE = 10
elif sys.platform == 'win32' or sys.platform == 'cygwin':
    MONO_FONT = 'Courier'
    FONT_SIZE = 10
elif sys.platform == 'darwin':
    MONO_FONT = 'Courier'
    FONT_SIZE = 13
else:
    MONO_FONT = 'Courier'
    FONT_SIZE = 13


