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

from libargos.collect.collector import FAKE_DIM_NAME
from libargos.config.groupcti import MainGroupCti
from libargos.config.boolcti import BoolCti
from libargos.config.choicecti import ChoiceCti
from libargos.config.intcti import IntCti
from libargos.inspector.abstract import AbstractInspector, UpdateReason

from libargos.qt import Qt, QtCore, QtGui
from libargos.utils.cls import to_string

logger = logging.getLogger(__name__)


def resizeAllSections(header, sectionSize):
    """ Sets all sections (columns or rows) of a header to the same section size.

        :param header: a QHeaderView
        :param sectionSize: the new size of the header section in pixels
    """
    for idx in range(header.length()):
        header.resizeSection(idx, sectionSize)



class TableInspectorCti(MainGroupCti):
    """ Configuration tree for a TableInspector
    """
    def __init__(self, nodeName, defaultData=None):

        super(TableInspectorCti, self).__init__(nodeName, defaultData=defaultData)

        self.insertChild(BoolCti("word wrap", True))
        self.insertChild(BoolCti("separate fields", True))

        self.autoResizeCellCti = self.insertChild(BoolCti("resize cells to contents", False,
                                                          childrenDisabledValue=True))

        # The initial values will be set in the constructor to the Qt defaults.
        self.defaultRowHeightCti = self.autoResizeCellCti.insertChild(
                IntCti("row height", -1, minValue=20, maxValue=500, stepSize=5))
        self.defaultColumnWidthCti = self.autoResizeCellCti.insertChild(
                IntCti("column width", -1, minValue=20, maxValue=500, stepSize=5))

        # Per pixel scrolling works better for large cells (e.g. containing XML strings).
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

        self._config = TableInspectorCti('inspector')

        if self.config.defaultRowHeightCti.configValue < 0: # If not yet initialized
            self.config.defaultRowHeightCti.data = verHeader.defaultSectionSize()
            self.config.defaultRowHeightCti.defaultData = verHeader.defaultSectionSize()

        if self.config.defaultColumnWidthCti.configValue < 0: # If not yet initialized
            self.config.defaultColumnWidthCti.data = horHeader.defaultSectionSize()
            self.config.defaultColumnWidthCti.defaultData = horHeader.defaultSectionSize()


    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple(['Y', 'X'])

    def _drawContents(self, reason=None, initiator=None):
        """ Draws the table contents from the sliced array of the collected repo tree item.

            See AbstractInspector.updateContents for the reason and initiator description.
        """
        logger.debug("TableInspector._drawContents: {}".format(self))

        self.model.updateState(self.collector.getSlicedArray(),
                               self.collector.rtiInfo,
                               self.configValue('separate fields'))

        scrollMode = self.configValue("scroll")
        self.tableView.setHorizontalScrollMode(scrollMode)
        self.tableView.setVerticalScrollMode(scrollMode)
        self.tableView.setWordWrap(self.configValue('word wrap'))

        # Only update the cell size when one of the relevant config values has changed because
        # resize to contents may be slow for large tables. Note that resetting the complete config
        # tree (by clicking the reset button of the inspector config tree item) might also change
        # the relevant config values. This is why we check with 'starts' with if a parent CTI
        # was clicked.
        if reason == UpdateReason.CONFIG_CHANGED and \
            (self.config.autoResizeCellCti.nodePath.startswith(initiator.nodePath) or
             self.config.defaultRowHeightCti.nodePath.startswith(initiator.nodePath) or
             self.config.defaultColumnWidthCti.nodePath.startswith(initiator.nodePath)):

            horHeader = self.tableView.horizontalHeader()
            verHeader = self.tableView.verticalHeader()

            if self.config.autoResizeCellCti.configValue:
                horHeader.setResizeMode(horHeader.ResizeToContents)
                verHeader.setResizeMode(horHeader.ResizeToContents)
            else:
                # First disable resize to contents, then resize the sections.
                horHeader.setResizeMode(horHeader.Interactive)
                verHeader.setResizeMode(horHeader.Interactive)
                resizeAllSections(horHeader, self.config.defaultColumnWidthCti.configValue)
                resizeAllSections(verHeader, self.config.defaultRowHeightCti.configValue)



class TableInspectorModel(QtCore.QAbstractTableModel):
    """ Qt table model that gives access to the sliced array,
        To be used in the TableInspector.
    """
    def __init__(self, parent = None):
        """ Constructor

            :param separateFields: If True the fields of a compound array (recArray) have their
                own separate cells.
            :param parent: parent Qt widget.
        """
        super(TableInspectorModel, self).__init__(parent)
        self._nRows = 0
        self._nCols = 0
        self._fieldNames = []
        self._slicedArray = None
        self._rtiInfo = {}

        self._separateFields = True  # User config option
        self._separateFieldOrientation = None # To store which axis is currently separated
        self._numbersInHeader = True


    def updateState(self, slicedArray, rtiInfo, separateFields):
        """ Sets the slicedArray and rtiInfo and other members. This will reset the model.

            Will be called from the tableInspector._drawContents.
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

            self._rtiInfo = rtiInfo
            self._separateFields = separateFields

            # Don't put numbers in the header if the record is of compound type, fields are
            # placed in separate cells and the fake dimension is selected (combo index 0)
            if self._separateFields and self._fieldNames:

                if self._rtiInfo['x-dim'] == FAKE_DIM_NAME:
                    self._separateFieldOrientation = Qt.Horizontal
                    self._numbersInHeader = False
                elif self._rtiInfo['y-dim'] == FAKE_DIM_NAME:
                    self._separateFieldOrientation = Qt.Vertical
                    self._numbersInHeader = False
                else:
                    self._separateFieldOrientation = Qt.Horizontal
                    self._numbersInHeader = True
            else:
                self._separateFieldOrientation = None
                self._numbersInHeader = True

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

            nFields = len(self._fieldNames)
            if self._separateFieldOrientation == Qt.Horizontal:
                cellValue = self._slicedArray[row, col // nFields][self._fieldNames[col % nFields]]
            elif self._separateFieldOrientation == Qt.Vertical:
                cellValue = self._slicedArray[row // nFields, col][self._fieldNames[row % nFields]]
            else:
                cellValue = self._slicedArray[row, col]

            # Numpy strings must be converted to regular strings,
            # otherwise they don't show up.
            return to_string(cellValue, bytes_encoding='utf-8')
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
            if self._separateFieldOrientation == orientation:

                nFields = len(self._fieldNames)
                varNr = section // nFields
                fieldNr = section % nFields
                header = str(varNr) + ' : ' if self._numbersInHeader else ''
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
        if self._separateFieldOrientation == Qt.Vertical:
            return self._nRows * len(self._fieldNames)
        else:
            return self._nRows


    def columnCount(self, parent=None):
        """ The number of columns of the sliced array.
            The 'parent' parameter can be a QModelIndex. It is ignored since the number of
            columns does not depend on the parent.
        """
        if self._separateFieldOrientation == Qt.Horizontal:
            return self._nCols * len(self._fieldNames)
        else:
            return self._nCols


