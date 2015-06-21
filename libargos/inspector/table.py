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

""" Contains TableInspector and TableInspectorModel
"""
import logging

from libargos.inspector.abstract import AbstractInspector
from libargos.qt import QtCore, QtGui

logger = logging.getLogger(__name__)


class TableInspectorModel(QtCore.QAbstractTableModel):
    """ Qt table model that gives access to the sliced array
    """
    def __init__(self, collector, parent = None):
        super(TableInspectorModel, self).__init__(parent)
        self._collector = collector
        self._nRows = 0
        self._nCols = 0   
        self._slicedArray = None
        
        
    def setSlicedArray(self, slicedArray):
        """ Sets the the sliced array
        """
        self.beginResetModel()
        try:
            self._slicedArray = slicedArray
            if slicedArray is None:
                self._nRows = 0
                self._nCols = 0
            else:
                self._nRows, self._nCols = self._slicedArray.shape
        finally:
            self.endResetModel()


    def data(self, index,  role = QtCore.Qt.DisplayRole):
        """ Returns the data at an index for a certain role
        """
        row = index.row()
        col = index.column()
        if (row < 0 or row >= self._nRows or col < 0 or col >= self._nCols): 
            return None

        # The check above should have returned None if the sliced array is None
        assert self._slicedArray is not None, "Sanity check failed." 
               
        if role == QtCore.Qt.DisplayRole:
            return repr(self._slicedArray[row, col])
        else:
            return None


    def flags(self, index):
        """ Returns the item flags for the given index.
        """
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


    def headerData(self, section, orientation, role):
        """ Returns the header for a section (row or column depending on orientation).
            Reimplemented from QAbstractTableModel to make the headers start at 0.
        """
        if role == QtCore.Qt.DisplayRole:
            return str(section)
        else:
            return None

    
    def rowCount(self, parent):
        """ The number of rows of the sliced array.
        """
        return self._nRows


    def columnCount(self, parent):
        """ The number of columns of the sliced array.
        """
        return self._nCols



class TableInspector(AbstractInspector):
    """ Shows the sliced array in a table.
    """
    def __init__(self, collector, parent=None):
        
        super(TableInspector, self).__init__(collector, parent=parent)
        
        self.model = TableInspectorModel(collector, parent=self)
        self.table = QtGui.QTableView()
        self.table.setModel(self.model)
        self.contentsLayout.addWidget(self.table)
        
    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple(['Rows', 'Columns'])
    
    def _updateRti(self):
        """ Draws the inspector widget when no input is available.
            The default implementation shows an error message. Descendants should override this.
        """
        logger.debug("TableInspector._updateRti: {}".format(self))
        slicedArray = self.collector.getSlicedArray()
        self.model.setSlicedArray(slicedArray)

