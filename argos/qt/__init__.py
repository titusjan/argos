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

""" Contains classes and functions based on Qt. These could in principle be useful for
    other projects but would then require minor tweaking (e.g. imports).
"""
# Import commonly used function into the package name space for convenience.

from argos.qt.misc import Qt, QtCore, QtGui, QtWidgets, QtSvg, QtSignal, QtSlot
from argos.qt.misc import initQApplication, initQCoreApplication
