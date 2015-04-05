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

""" Base class for inspectors consisting of a single QTableWidget
"""
import logging
from .base import BaseInspector
from libargos.qt import QtGui
from libargos.qt.togglecolumn import ToggleColumnTableWidget

logger = logging.getLogger(__name__)


class BaseTableInspector(BaseInspector):
    """ Base class for inspectors that consist of a single QTableWidget
    """
    _label = "Abstract Table Inspector"
    
    def __init__(self, columnLabels, parent=None):
        super(BaseTableInspector, self).__init__(parent)

        assert len(columnLabels) > 0, "column_labels is not defined"
        self._columnLabels = columnLabels if columnLabels is not None else []
        
        self.table = ToggleColumnTableWidget(5, 2)
        self.contentsLayout.addWidget(self.table)
        
        self.table.setWordWrap(True)
        #self.table.setTextElideMode(QtCore.Qt.ElideNone)
        self.table.setColumnCount(len(self._columnLabels))
        self.table.setHorizontalHeaderLabels(self._columnLabels)
        self.table.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.table.verticalHeader().hide()        
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        
        self.table.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)

        tableHeader = self.table._horizontalHeader() # TODO
        tableHeader.setResizeMode(QtGui.QHeaderView.Interactive) # don't set to stretch
        tableHeader.setStretchLastSection(True)
        
            