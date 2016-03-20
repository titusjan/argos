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

from libargos.config.groupcti import MainGroupCti
from libargos.config.boolcti import BoolCti
from libargos.inspector.abstract import AbstractInspector

from libargos.qt import Qt, QtCore, QtGui

logger = logging.getLogger(__name__)



class TableInspectorCti(MainGroupCti):
    """ Configuration tree for a PgLinePlot1d inspector
    """
    def __init__(self, nodeName, defaultData=None):

        super(TableInspectorCti, self).__init__(nodeName, defaultData=defaultData)

        self.insertChild(BoolCti("separate fields", True))
        self.insertChild(BoolCti("resize to contents", True))



class TableInspector(AbstractInspector):
    """ Shows the sliced array in a table.
    """
    def __init__(self, collector, parent=None):

        super(TableInspector, self).__init__(collector, parent=parent)

        self.model = TableInspectorModel(parent=self)
        self.tableView = QtGui.QTableView()
        self.contentsLayout.addWidget(self.tableView)
        self.tableView.setModel(self.model)
        self.tableView.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.tableView.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

        self._config = TableInspectorCti('inspector')


    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple(['Y', 'X'])


    def _drawContents(self):
        """ Draws the inspector widget when no input is available.
            The default implementation shows an error message. Descendants should override this.
        """
        logger.debug("TableInspector._drawContents: {}".format(self))
        slicedArray = self.collector.getSlicedArray()

        self.model.separateFields = self.configValue('separate fields')
        self.model.setSlicedArray(slicedArray)

        horHeader = self.tableView.horizontalHeader()
        if self.configValue("resize to contents"):
            horHeader.setResizeMode(horHeader.ResizeToContents)
        else:
            horHeader.setResizeMode(horHeader.Interactive)





class TableInspectorModel(QtCore.QAbstractTableModel):
    """ Qt table model that gives access to the sliced array
    """
    def __init__(self, separateFields=True, parent = None):
        """ Constructor

        :param separateFields: If True the fields of a compound array (recArray) have their
            own separate cells.
        :param parent: parent Qt widget. 
        """
        super(TableInspectorModel, self).__init__(parent)
        self.separateFields = separateFields
        self._nRows = 0
        self._nCols = 0
        self._fieldNames = []
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
                self._fieldNames = []
            else:
                self._nRows, self._nCols = self._slicedArray.shape
                if self._slicedArray.dtype.names:
                    self._fieldNames = self._slicedArray.dtype.names
                else:
                    self._fieldNames = []
        finally:
            self.endResetModel()


    def data(self, index, role = Qt.DisplayRole):
        """ Returns the data at an index for a certain role
        """
        row = index.row()
        col = index.column()
        if (row < 0 or row >= self.rowCount() or col < 0 or col >= self.columnCount()):
            return None

        # The check above should have returned None if the sliced array is None
        assert self._slicedArray is not None, "Sanity check failed." 
               
        if role == Qt.DisplayRole:
            if self.separateFields and self._fieldNames:
                nFields = len(self._fieldNames)
                varNr = col // nFields
                fieldNr = col % nFields
                return repr(self._slicedArray[row, varNr][self._fieldNames[fieldNr]])
            else:
                return repr(self._slicedArray[row, col])
        else:
            return None


    def flags(self, index):
        """ Returns the item flags for the given index.
        """
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def headerData(self, section, orientation, role):
        """ Returns the header for a section (row or column depending on orientation).
            Reimplemented from QAbstractTableModel to make the headers start at 0.
        """
        if role == Qt.DisplayRole:
            if self.separateFields and orientation == Qt.Horizontal and self._fieldNames:
                nFields = len(self._fieldNames)
                varNr = section // nFields
                fieldNr = section % nFields
                header = str(varNr) + ' : ' if self._nCols > 1 else ' : '
                header += self._fieldNames[fieldNr]
                return header
            else:
                return str(section)
        else:
            return None

    
    def rowCount(self, parent=None):
        """ The number of rows of the sliced array.
            The 'parent' parameter can be a QModelIndex. It is ignored since the number of
            rows does not depend on the parent.
        """
        return self._nRows


    def columnCount(self, parent=None):
        """ The number of columns of the sliced array.
            The 'parent' parameter can be a QModelIndex. It is ignored since the number of
            columns does not depend on the parent.
        """
        if self.separateFields and self._fieldNames:
            return self._nCols * len(self._fieldNames)
        else:
            return self._nCols


