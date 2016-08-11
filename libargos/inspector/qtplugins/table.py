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
from libargos.config.qtctis import FontCti
from libargos.inspector.abstract import AbstractInspector, UpdateReason
from libargos.utils.cls import check_class

from libargos.qt import Qt, QtCore, QtGui
from libargos.utils.cls import to_string

logger = logging.getLogger(__name__)

FIXED_HEADERS_AT_SIZE = 10000 # If header has more elements, the headers size CTIs are disabled.


def resizeAllSections(header, sectionSize):
    """ Sets all sections (columns or rows) of a header to the same section size.

        :param header: a QHeaderView
        :param sectionSize: the new size of the header section in pixels
    """
    for idx in range(header.length()):
        header.resizeSection(idx, sectionSize)



class TableInspectorCti(MainGroupCti):
    """ Configuration tree item for a TableInspector
    """
    def __init__(self, tableInspector, nodeName):

        super(TableInspectorCti, self).__init__(nodeName)

        check_class(tableInspector, TableInspector)
        self.tableInspector = tableInspector

        self.insertChild(BoolCti("word wrap", True))
        self.insertChild(BoolCti("separate fields", True))

        # The defaultRowHeightCti and defaultColWidthCti are initialized with -1; they will get
        # the actual values in the TableInspector contructor.
        self.autoRowHeightCti = self.insertChild(BoolCti("auto row heights", False,
                                                        childrenDisabledValue=True))
        self.defaultRowHeightCti = self.autoRowHeightCti.insertChild(
            IntCti("row height", -1, minValue=20, maxValue=500, stepSize=5))

        self.autoColWidthCti = self.insertChild(BoolCti("auto column widths", False,
                                                        childrenDisabledValue=True))
        self.defaultColWidthCti = self.autoColWidthCti.insertChild(
            IntCti("column width", -1, minValue=20, maxValue=500, stepSize=5))

        # Per pixel scrolling works better for large cells (e.g. containing XML strings).
        self.insertChild(ChoiceCti("scroll", displayValues=["per cell", "per pixel"],
                                   configValues=[QtGui.QAbstractItemView.ScrollPerItem,
                                                 QtGui.QAbstractItemView.ScrollPerPixel]))

        self.encodingCti = self.insertChild(
            ChoiceCti('encoding', editable=True,
                      configValues=['utf-8', 'ascii', 'latin-1', 'windows-1252']))

        self.fontCti = self.insertChild(FontCti(self.tableInspector, "font",
                                                defaultData=QtGui.QFont('Courier', 14)))


    def _refreshNodeFromTarget(self):
        """ Refreshes the TableInspectorCti from the TableInspector target it monitors.

            Disables the row heights and column width items if the headers are too large. Otherwise
            the resizeing may take to long and the program will hang.
        """
        # Disable row height and column with settings for large headers (too slow otherwise)
        tableModel = self.tableInspector.model
        self.autoRowHeightCti.enableBranch(tableModel.rowCount() < FIXED_HEADERS_AT_SIZE)
        self.autoColWidthCti.enableBranch(tableModel.columnCount() < FIXED_HEADERS_AT_SIZE)

        self.model.emitDataChanged(self.autoRowHeightCti)
        self.model.emitDataChanged(self.autoColWidthCti)

        logger.debug("ROW COUNT: {} -> enabled {}".format(tableModel.rowCount(), self.autoRowHeightCti.enabled))
        logger.debug("COL COUNT: {} -> enabled {}".format(tableModel.columnCount(), self.autoColWidthCti.enabled))





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

        self._config = TableInspectorCti(tableInspector=self, nodeName='inspector')

        if self.config.defaultRowHeightCti.configValue < 0: # If not yet initialized
            self.config.defaultRowHeightCti.data = verHeader.defaultSectionSize()
            self.config.defaultRowHeightCti.defaultData = verHeader.defaultSectionSize()

        if self.config.defaultColWidthCti.configValue < 0: # If not yet initialized
            self.config.defaultColWidthCti.data = horHeader.defaultSectionSize()
            self.config.defaultColWidthCti.defaultData = horHeader.defaultSectionSize()


    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple(['Y', 'X'])


    def getFont(self):
        """ Returns the font of the table model. Can be a QFont or None if no font is set.
        """
        return self.model.getFont()


    def setFont(self, font):
        """ Sets the font of the table model. Can be a QFont or None if no font is set.
        """
        return self.model.setFont(font)


    def _drawContents(self, reason=None, initiator=None):
        """ Draws the table contents from the sliced array of the collected repo tree item.

            See AbstractInspector.updateContents for the reason and initiator description.
        """
        logger.debug("TableInspector._drawContents: {}".format(self))

        self.model.updateState(self.collector.getSlicedArray(),
                               self.collector.rtiInfo,
                               self.configValue('separate fields'))

        self.model.encoding = self.config.encodingCti.configValue

        scrollMode = self.configValue("scroll")
        self.tableView.setHorizontalScrollMode(scrollMode)
        self.tableView.setVerticalScrollMode(scrollMode)
        self.tableView.setWordWrap(self.configValue('word wrap'))

        # Update the model font from the font config item (will call self.setFont)
        self.config.updateTarget()


        # Only update the cell size when one of the relevant config values has changed because
        # resize to contents may be slow for large tables. Note that resetting the complete config
        # tree (by clicking the reset button of the inspector config tree item) might also change
        # the relevant config values. This is why we check with 'starts' with if a parent CTI
        # was clicked.

        verHeader = self.tableView.verticalHeader()

        logger.info("ADAPTING VERTICAL HEADER")
        if self.config.autoRowHeightCti.configValue:
            numCells = self.model.rowCount() * self.model.columnCount()
            if numCells <= 1000:
                logger.debug("setting vertical resize mode to ResizeToContents")
                verHeader.setResizeMode(QtGui.QHeaderView.ResizeToContents)
            else:
                if self.model.rowCount() < FIXED_HEADERS_AT_SIZE:
                    # ResizeToContents can be very slow because it gets all rows.
                    # Work around: resize only first row and columns and apply this to all rows/cols
                    logger.warning("Performance work around: for tables with more than 1000 cells the only the first row and columns are resized")
                    verHeader.setResizeMode(QtGui.QHeaderView.Interactive)
                    self.tableView.resizeRowToContents(0)
                    resizeAllSections(verHeader, self.tableView.rowHeight(0))
                else:
                    logger.debug("Row resizing will be disabled. Don't resize here")

        else:
            # First disable resize to contents, then resize the sections.
            verHeader.setResizeMode(QtGui.QHeaderView.Interactive)
            if reason == UpdateReason.CONFIG_CHANGED and \
                (self.config.autoRowHeightCti.nodePath.startswith(initiator.nodePath) or
                 self.config.defaultRowHeightCti.nodePath.startswith(initiator.nodePath)):

                logger.debug("setting all vertical sections to: {}".format(self.config.defaultRowHeightCti.configValue))
                resizeAllSections(verHeader, self.config.defaultRowHeightCti.configValue)
            else:
                logger.debug("Nothing needed")


        horHeader = self.tableView.horizontalHeader()

        logger.info("ADAPTING HORIZONTAL HEADER")
        if self.config.autoColWidthCti.configValue:
            numCells = self.model.rowCount() * self.model.columnCount()
            if numCells <= 1000:
                logger.debug("setting horizontal resize mode to ResizeToContents")
                horHeader.setResizeMode(QtGui.QHeaderView.ResizeToContents)
            else:
                if self.model.columnCount() < FIXED_HEADERS_AT_SIZE:
                    # ResizeToContents can be very slow because it gets all rows.
                    # Work around: resize only first row and columns and apply this to all rows/cols
                    logger.warning("Performance work around: for tables with more than 1000 cells the only the first row and columns are resized")
                    horHeader.setResizeMode(QtGui.QHeaderView.Interactive)
                    self.tableView.resizeColumnToContents(0)
                    resizeAllSections(horHeader, self.tableView.columnWidth(0))
                else:
                    logger.debug("Column resizing will be disabled. Don't resize here")
        else:
            # First disable resize to contents, then resize the sections.
            horHeader.setResizeMode(QtGui.QHeaderView.Interactive)

            if reason == UpdateReason.CONFIG_CHANGED and \
                (self.config.autoColWidthCti.nodePath.startswith(initiator.nodePath) or
                 self.config.defaultColWidthCti.nodePath.startswith(initiator.nodePath)):

                logger.debug("setting all horizontal sections to: {}".format(self.config.defaultColWidthCti.configValue))
                resizeAllSections(horHeader, self.config.defaultColWidthCti.configValue)
            else:
                logger.debug("Nothing needed")






        # # Only update the cell size when one of the relevant config values has changed because
        # # resize to contents may be slow for large tables. Note that resetting the complete config
        # # tree (by clicking the reset button of the inspector config tree item) might also change
        # # the relevant config values. This is why we check with 'starts' with if a parent CTI
        # # was clicked.
        # if reason == UpdateReason.CONFIG_CHANGED and \
        #     (self.config.autoResizeCellCti.nodePath.startswith(initiator.nodePath) or
        #      self.config.defaultRowHeightCti.nodePath.startswith(initiator.nodePath) or
        #      self.config.defaultColumnWidthCti.nodePath.startswith(initiator.nodePath) or
        #      self.config.fontCti.nodePath.startswith(initiator.nodePath) or
        #      self.config.encodingCti.nodePath.startswith(initiator.nodePath)):
        #
        #     horHeader = self.tableView.horizontalHeader()
        #     verHeader = self.tableView.verticalHeader()
        #
        #     if self.config.autoResizeCellCti.configValue:
        #         numCells = self.model.rowCount() * self.model.columnCount()
        #         if numCells <= 1000:
        #             horHeader.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        #             verHeader.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        #         else:
        #             # ResizeToContents can be very slow because it gets all rows.
        #             # Work around: resize only first row and columns and apply this to all rows/cols
        #
        #             logger.warning("Performance work around: for tables with more than 1000 cells the only the first row and columns are resized")
        #             horHeader.setResizeMode(QtGui.QHeaderView.Interactive)
        #             verHeader.setResizeMode(QtGui.QHeaderView.Interactive)
        #             self.tableView.resizeColumnToContents(0)
        #             resizeAllSections(horHeader, self.tableView.columnWidth(0))
        #             self.tableView.resizeRowToContents(0)
        #             resizeAllSections(verHeader, self.tableView.rowHeight(0))
        #     else:
        #         # First disable resize to contents, then resize the sections.
        #         horHeader.setResizeMode(QtGui.QHeaderView.Interactive)
        #         verHeader.setResizeMode(QtGui.QHeaderView.Interactive)
        #         resizeAllSections(horHeader, self.config.defaultColumnWidthCti.configValue)
        #         resizeAllSections(verHeader, self.config.defaultRowHeightCti.configValue)



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
        self._font = None # Default font

        self.encoding = 'utf-8' # can be a simple attibute


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

            # Numpy strings must be converted to regular strings, otherwise they don't show up.
            return to_string(cellValue, decode_bytes=self.encoding)

        elif role == Qt.FontRole:
            assert self._font
            return self._font

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


    def getFont(self):
        """ Returns the font that will be returned when data() is called with the Qt.FontRole.
            Can be a QFont or None if no font is set.
        """
        return self._font


    def setFont(self, font):
        """ Sets the font that will be returned when data() is called with the Qt.FontRole.
            Can be a QFont or None if no font is set.
        """
        check_class(font, QtGui.QFont, allow_none=True)
        self._font = font
