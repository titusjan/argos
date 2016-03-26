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
from libargos.config.choicecti import ChoiceCti
from libargos.config.intcti import IntCti
from libargos.inspector.abstract import AbstractInspector

from libargos.qt import Qt, QtCore, QtGui
from libargos.utils.cls import is_a_string, is_a_numpy_string

logger = logging.getLogger(__name__)


def resizeAllSections(header, sectionSize):
    """ Sets all sections (columns or rows) of a header to the same section size.

        :param header: a QHeaderView
        :param sectionSize: the new size of the header section in pixels
    """
    for idx in range(header.length()):
        header.resizeSection(idx, sectionSize)



class TableInspectorCti(MainGroupCti):
    """ Configuration tree for a PgLinePlot1d inspector
    """
    def __init__(self, nodeName, defaultData=None):

        super(TableInspectorCti, self).__init__(nodeName, defaultData=defaultData)

        self.insertChild(BoolCti("word wrap", True))
        self.insertChild(BoolCti("separate fields", True))

        self.cell_auto_resize = self.insertChild(BoolCti("resize cells to contents", False,
                                                         childrenDisabledValue=True))

        # The initial values will be set in the constructor to the Qt defaults.
        self.defaultRowHeight = self.cell_auto_resize.insertChild(
                IntCti("row height", -1, minValue=20, maxValue=500, stepSize=5))
        self.defaultColumnWidth = self.cell_auto_resize.insertChild(
                IntCti("column width", -1, minValue=20, maxValue=500, stepSize=5))


        self.insertChild(ChoiceCti("scroll", displayValues=["per cell", "per pixel"],
                                   configValues=[QtGui.QAbstractItemView.ScrollPerItem,
                                                 QtGui.QAbstractItemView.ScrollPerPixel]))

class TableInspector(AbstractInspector):
    """ Shows the sliced array in a table.
    """
    def __init__(self, collector, parent=None):

        super(TableInspector, self).__init__(collector, parent=parent)

        self.model = TableInspectorModel(parent=self)
        self.tableView = QtGui.QTableView()
        self.contentsLayout.addWidget(self.tableView)
        self.tableView.setModel(self.model)

        horHeader = self.tableView.horizontalHeader()
        verHeader = self.tableView.verticalHeader()
        horHeader.setCascadingSectionResizes(False)
        verHeader.setCascadingSectionResizes(False)

        # Some fields to keep track of old value to detect changes.
        # TODO: refactor when _drawContents has 'cause' parameter
        self._resizeToContents = None
        self._defaultRowHeight = None
        self._defaultColumnWidth = None

        self._config = TableInspectorCti('inspector')

        if self.config.defaultRowHeight.configValue < 0: # If not yet initialized
            self.config.defaultRowHeight.data = verHeader.defaultSectionSize()
            self.config.defaultRowHeight.defaultData = verHeader.defaultSectionSize()

        if self.config.defaultColumnWidth.configValue < 0: # If not yet initialized
            self.config.defaultColumnWidth.data = horHeader.defaultSectionSize()
            self.config.defaultColumnWidth.defaultData = horHeader.defaultSectionSize()


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

        # Per pixel scrolling works better for large cells (e.g. containing XML strings).
        scrollMode = self.configValue("scroll")
        self.tableView.setHorizontalScrollMode(scrollMode)
        self.tableView.setVerticalScrollMode(scrollMode)
        self.tableView.setWordWrap(self.configValue('word wrap'))
        self.model.separateFields = self.configValue('separate fields')
        self.model.setSlicedArray(slicedArray)

        # Don't put numbers in the header if the record is of compound type, a fields are
        # placed in separate cells and the fake dimension is selected (combo index 0)
        rtiInfo = self.collector.getRtiInfo()
        self.model.numbersInHeaderX = rtiInfo and rtiInfo['x-dim'] != self.collector.FAKE_DIM_NAME

        if (self.config.cell_auto_resize.configValue != self._resizeToContents or
            self.config.defaultColumnWidth.configValue != self._defaultColumnWidth or
            self.config.defaultRowHeight.configValue != self._defaultRowHeight):

            self._resizeToContents = self.config.cell_auto_resize.configValue
            self._defaultRowHeight = self.config.defaultRowHeight.configValue
            self._defaultColumnWidth = self.config.defaultColumnWidth.configValue

            horHeader = self.tableView.horizontalHeader()
            verHeader = self.tableView.verticalHeader()

            if self._resizeToContents:
                horHeader.setResizeMode(horHeader.ResizeToContents)
                verHeader.setResizeMode(horHeader.ResizeToContents)
            else:
                # First disable resize to contents, then resize the sections.
                horHeader.setResizeMode(horHeader.Interactive)
                verHeader.setResizeMode(horHeader.Interactive)
                resizeAllSections(horHeader, self.config.defaultColumnWidth.configValue)
                resizeAllSections(verHeader, self.config.defaultRowHeight.configValue)



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
        self.numbersInHeaderX = True
        self.numbersInHeaderY = True # not used yet
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
                cellValue = self._slicedArray[row, varNr][self._fieldNames[fieldNr]]
            else:
                cellValue = self._slicedArray[row, col]

            if is_a_string(cellValue):
                # Numpy strings must be converted to regular strings,
                # otherwise they don't show up.
                return unicode(cellValue)
            else:
                return repr(cellValue)

            # if is_a_numpy_string(cellValue):
            #     return unicode(cellValue)
            # elif is_a_string(cellValue):
            #     return cellValue
            # else:
            #     return repr(cellValue)

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
                header = str(varNr) + ' : ' if self.numbersInHeaderX else ''
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


