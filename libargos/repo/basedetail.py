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

""" Base class for inspectors
"""
import logging
from libargos.qt import QtCore, QtGui
from libargos.qt.togglecolumn import ToggleColumnTableWidget
from libargos.widgets.constants import DOCK_SPACING, DOCK_MARGIN, LEFT_DOCK_WIDTH
from libargos.widgets.display import MessageDisplay

logger = logging.getLogger(__name__)


class BaseDetailPane(QtGui.QStackedWidget):
    """ Base class for plugins that show details of the current repository tree item.
        Serves as an interface but can also be instantiated for debugging purposes.
        A detail pane is a stacked widget; it has a contents page and and error page.
    """
    _label = "Details"
    
    ERROR_PAGE_IDX = 0
    CONTENTS_PAGE_IDX = 1
    
    def __init__(self, parent=None):
        
        super(BaseDetailPane, self).__init__(parent)

        self.errorWidget = MessageDisplay()
        self.addWidget(self.errorWidget)

        self.contentsWidget = QtGui.QWidget()
        self.addWidget(self.contentsWidget)

        self.contentsLayout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
        self.contentsLayout.setSpacing(DOCK_SPACING)
        self.contentsLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)        
        self.contentsWidget.setLayout(self.contentsLayout)
        
        self.setCurrentIndex(self.CONTENTS_PAGE_IDX)

    @classmethod
    def classLabel(cls):
        """ Returns a short string that describes this class. For use in menus, headers, etc. 
        """
        return cls._label
        
    def sizeHint(self):
        """ The recommended size for the widget."""
        return QtCore.QSize(LEFT_DOCK_WIDTH, 250)
          

    def drawEmpty(self):
        """ Draws the inspector widget when no input is available.
            The default implementation shows an error message. Descendants should override this.
        """
        self.setCurrentIndex(self.CONTENTS_PAGE_IDX)
        

    def drawError(self, msg="", title="Error"):
        """ Shows and error message
        """
        self.errorWidget.setError(msg=msg, title=title)
        self.setCurrentIndex(self.ERROR_PAGE_IDX)
        
        
    
class TableDetailPane(BaseDetailPane):
    """ Base class for inspectors that consist of a single QTableWidget
    """
    _label = "Details Table"
    
    def __init__(self, columnLabels, parent=None):
        super(TableDetailPane, self).__init__(parent)

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

        tableHeader = self.table.horizontalHeader()
        tableHeader.setResizeMode(QtGui.QHeaderView.Interactive) # don't set to stretch
        tableHeader.setStretchLastSection(True)
        
            
        