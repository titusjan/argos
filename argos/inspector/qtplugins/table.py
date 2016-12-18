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
import numbers

import numpy as np

from argos.external import six
from argos.collect.collector import FAKE_DIM_NAME
from argos.config.boolcti import BoolCti
from argos.config.choicecti import ChoiceCti
from argos.config.groupcti import GroupCti, MainGroupCti
from argos.config.intcti import IntCti
from argos.config.qtctis import FontCti, ColorCti
from argos.info import DEBUGGING
from argos.inspector.abstract import AbstractInspector
from argos.qt import Qt, QtCore, QtGui, QtWidgets
from argos.widgets.constants import MONO_FONT, FONT_SIZE
from argos.utils.cls import check_class, check_is_a_string
from argos.utils.cls import to_string, is_an_array
from argos.utils.misc import is_quoted

logger = logging.getLogger(__name__)

RESET_HEADERS_AT_SIZE = 10000   # If header has more elements, the headers size CTIs are disabled.
OPTIMIZE_RESIZE_AT_SIZE = 1000  # If the table has more elements, only the current column/row are
                                # resized and the others take the same size

ALIGN_SMART = -1  # Use right alignment for numbers and left alignment for everything else.

def resizeAllSections(header, sectionSize):
    """ Sets all sections (columns or rows) of a header to the same section size.

        :param header: a QHeaderView
        :param sectionSize: the new size of the header section in pixels
    """
    for idx in range(header.length()):
        header.resizeSection(idx, sectionSize)


def makeReplacementField(formatSpec, altFormatSpec='', testValue=None):
    """ Prepends a colon and wraps the formatSpec in curly braces to yield a replacement field.

        The format specification is part of a replacement field, which can be used in new-style
        string formatting. See:
            https://docs.python.org/3/library/string.html#format-string-syntax
            https://docs.python.org/3/library/string.html#format-specification-mini-language

        If the formatSpec does not contain a a color or exclamation mark, a colon is prepended.

        If the formatSpec starts and end in quotes (single or double) only the quotes are removed,
        no curly braces or colon charactes are added. This allows users to define a format spec.

        :param formatSpec: e.g. '5.2f' will return '{:5.2f}'
        :param altFormatSpec: alternative that will be used if the formatSpec evaluates to False
        :param testValue: if not None, result.format(testValue) will be evaluated as a test.
        :return: string
    """
    check_is_a_string(formatSpec)
    check_is_a_string(altFormatSpec)
    fmt = altFormatSpec if not formatSpec else formatSpec

    if is_quoted(fmt):
        fmt = fmt[1:-1] # remove quotes
    else:
        if fmt and ':' not in fmt and '!' not in fmt:
            fmt = ':' + fmt
        fmt = '{' + fmt + '}'

    # Test resulting replacement field
    if testValue is not None:
        try:
            _dummy = fmt.format(testValue)
        except Exception:
            msg = ("Format specifier failed: replacement-field={!r}, test-value={!r}"
                   .format(fmt, testValue))
            logger.error(msg)
            raise ValueError(msg)

    logger.debug("Resulting replacement field: {!r}".format(fmt))
    return fmt



class TableInspectorCti(MainGroupCti):
    """ Configuration tree item for a TableInspector
    """
    def __init__(self, tableInspector, nodeName):

        super(TableInspectorCti, self).__init__(nodeName)

        check_class(tableInspector, TableInspector)
        self.tableInspector = tableInspector

        # The defaultRowHeightCti and defaultColWidthCti are initialized with -1; they will get
        # the actual values in the TableInspector constructor.
        self.autoRowHeightCti = self.insertChild(BoolCti("auto row heights", False,
                                                        childrenDisabledValue=True))
        self.defaultRowHeightCti = self.autoRowHeightCti.insertChild(
            IntCti("row height", -1, minValue=20, maxValue=500, stepSize=5))

        self.autoColWidthCti = self.insertChild(BoolCti("auto column widths", False,
                                                        childrenDisabledValue=True))
        self.defaultColWidthCti = self.autoColWidthCti.insertChild(
            IntCti("column width", -1, minValue=20, maxValue=500, stepSize=5))

        self.insertChild(BoolCti("separate fields", True))
        self.insertChild(BoolCti("word wrap", False))

        self.encodingCti = self.insertChild(
            ChoiceCti('encoding', editable=True,
                      configValues=['utf-8', 'ascii', 'latin-1', 'windows-1252']))

        fmtCti = self.insertChild(GroupCti("format specifiers"))

        # Use '!r' as default for Python 2. This will convert the floats with repr(), which is
        # necessary because str() or an empty format string will only print 2 decimals behind the
        # point. In Python 3 this is not necessary: all relevant decimals are printed.
        numDefaultValue = 6 if six.PY2 else 0

        self.strFormatCti = fmtCti.insertChild(
            ChoiceCti("strings", 0, editable=True, completer=None,
                      configValues=['', 's', '!r', '!a',
                                    '10.10s', '_<15s', '_>15s', "'str: {}'"]))

        self.intFormatCti = fmtCti.insertChild(
            ChoiceCti("integers", 0, editable=True, completer=None,
                      configValues=['', 'd', 'n', 'c', '#b', '#o', '#x', '!r',
                                    '8d', '#8.4g', '_<10', '_>10', "'int: {}'"]))

        self.numFormatCti = fmtCti.insertChild(
            ChoiceCti("other numbers", numDefaultValue, editable=True, completer=None,
                      configValues=['', 'f', 'g', 'n', '%', '!r',
                                    '8.3e', '#8.4g', '_<15', '_>15', "'num: {}'"]))

        self.otherFormatCti = fmtCti.insertChild(
            ChoiceCti("other types", 0, editable=True, completer=None,
                      configValues=['', '!s', '!r', "'other: {}'"]))

        self.maskFormatCti = fmtCti.insertChild(
            ChoiceCti("missing data", 2, editable=True, completer=None,
                      configValues=['', "' '", "'--'", "'<masked>'", '!r']))

        self.fontCti = self.insertChild(FontCti(self.tableInspector, "font",
                                                defaultData=QtGui.QFont(MONO_FONT, FONT_SIZE)))

        self.dataColorCti = self.insertChild(
            ColorCti('text color', QtGui.QColor('#000000')))

        self.missingColorCti = self.insertChild(
            ColorCti('missing data color', QtGui.QColor('#B0B0B0')))

        self.horAlignCti = self.insertChild(
            ChoiceCti('horizontal alignment',
                      configValues=[ALIGN_SMART, Qt.AlignLeft, Qt.AlignHCenter, Qt.AlignRight],
                      displayValues=['Type-dependent', 'Left', 'Center', 'Right']))
                      # Qt.AlignJustify not included, it doesn't seem to do anything,

        self.verAlignCti = self.insertChild(
            ChoiceCti('vertical alignment', defaultData=1,
                      configValues=[Qt.AlignTop, Qt.AlignVCenter, Qt.AlignBottom],
                      displayValues=['Top', 'Center', 'Bottom']))

        # Per pixel scrolling works better for large cells (e.g. containing XML strings).
        self.insertChild(ChoiceCti("scroll", displayValues=["Per cell", "Per pixel"],
                                   configValues=[QtWidgets.QAbstractItemView.ScrollPerItem,
                                                 QtWidgets.QAbstractItemView.ScrollPerPixel]))


    def _refreshNodeFromTarget(self):
        """ Refreshes the TableInspectorCti from the TableInspector target it monitors.

            Disables auto-sizing of the header sizes for very large headers (> 10000 elements).
            Otherwise the resizing may take to long and the program will hang.
        """
        tableModel = self.tableInspector.model

        # Disable row height and column with settings for large headers (too slow otherwise)
        if tableModel.rowCount() >= RESET_HEADERS_AT_SIZE:
            self.autoRowHeightCti.data = False
            self.model.emitDataChanged(self.autoRowHeightCti)
            self.autoRowHeightCti.enable = False
        else:
            self.autoRowHeightCti.enable = True

        if tableModel.columnCount() >= RESET_HEADERS_AT_SIZE:
            self.autoColWidthCti.data  = False
            self.model.emitDataChanged(self.autoColWidthCti)
            self.autoColWidthCti.enable = False
        else:
            self.autoColWidthCti.enable = True



class TableInspector(AbstractInspector):
    """ Shows the sliced array in a table.
    """
    def __init__(self, collector, parent=None):

        super(TableInspector, self).__init__(collector, parent=parent)

        self.model = TableInspectorModel(parent=self)
        self.tableView = QtWidgets.QTableView()
        self.contentsLayout.addWidget(self.tableView)
        self.tableView.setModel(self.model)
        self.tableView.setSelectionMode(QtWidgets.QTableView.ContiguousSelection)

        horHeader = self.tableView.horizontalHeader()
        verHeader = self.tableView.verticalHeader()
        horHeader.setCascadingSectionResizes(False)
        verHeader.setCascadingSectionResizes(False)

        self._config = TableInspectorCti(tableInspector=self, nodeName='table')

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


    def _clearContents(self):
        """ Clears the  the inspector widget when no valid input is available.
        """
        pass


    def _drawContents(self, reason=None, initiator=None):
        """ Draws the table contents from the sliced array of the collected repo tree item.

            See AbstractInspector.updateContents for the reason and initiator description.
        """
        logger.debug("TableInspector._drawContents: {}".format(self))

        oldTableIndex = self.tableView.currentIndex()
        if oldTableIndex.isValid():
            selectionWasValid = True # Defensive programming, keep old value just in case
            oldRow = oldTableIndex.row()
            oldCol = oldTableIndex.column()
        else:
            selectionWasValid = False
            oldRow = 0
            oldCol = 0

        self.model.updateState(self.collector.getSlicedArray(),
                               self.collector.rtiInfo,
                               self.configValue('separate fields'))

        self.model.encoding = self.config.encodingCti.configValue
        self.model.horAlignment = self.config.horAlignCti.configValue
        self.model.verAlignment = self.config.verAlignCti.configValue
        self.model.dataColor = self.config.dataColorCti.configValue
        self.model.missingColor = self.config.missingColorCti.configValue

        self.model.strFormat   = makeReplacementField(self.config.strFormatCti.configValue,
                                                      testValue='my_string')
        self.model.intFormat   = makeReplacementField(self.config.intFormatCti.configValue,
                                                      testValue=0)
        self.model.numFormat   = makeReplacementField(self.config.numFormatCti.configValue,
                                                      testValue=0.0)
        self.model.otherFormat = makeReplacementField(self.config.otherFormatCti.configValue,
                                                      testValue=None)
        self.model.maskFormat  = makeReplacementField(self.config.maskFormatCti.configValue,
                                                      testValue=None)

        scrollMode = self.configValue("scroll")
        self.tableView.setHorizontalScrollMode(scrollMode)
        self.tableView.setVerticalScrollMode(scrollMode)
        self.tableView.setWordWrap(self.configValue('word wrap'))

        # Update the model font from the font config item (will call self.setFont)
        self.config.updateTarget()

        verHeader = self.tableView.verticalHeader()
        if (self.config.autoRowHeightCti.configValue
            and self.model.rowCount() < RESET_HEADERS_AT_SIZE):

            numCells = self.model.rowCount() * self.model.columnCount()
            if numCells <= OPTIMIZE_RESIZE_AT_SIZE:
                logger.debug("Setting vertical resize mode to ResizeToContents")
                verHeader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            else:
                # ResizeToContents can be very slow because it gets all rows.
                # Work around: resize only first row and columns and apply this to all rows/cols
                # TODO: perhaps use SizeHintRole?
                logger.warning("Performance work around: for tables with more than 1000 cells " +
                               "only the current row is resized and the others use that size.")
                verHeader.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
                self.tableView.resizeRowToContents(oldRow)
                resizeAllSections(verHeader, self.tableView.rowHeight(oldRow))
        else:
            logger.debug("Setting vertical resize mode to Interactive and reset header")
            verHeader.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
            verHeader.setDefaultSectionSize(self.config.defaultRowHeightCti.configValue)
            verHeader.reset()

        horHeader = self.tableView.horizontalHeader()
        if (self.config.autoColWidthCti.configValue
            and self.model.columnCount() < RESET_HEADERS_AT_SIZE):

            numCells = self.model.rowCount() * self.model.columnCount()
            if numCells <= OPTIMIZE_RESIZE_AT_SIZE:
                logger.debug("setting horizontal resize mode to ResizeToContents")
                horHeader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            else:
                # ResizeToContents can be very slow because it gets all rows.
                # Work around: resize only first row and columns and apply this to all rows/cols
                # TODO: perhaps use SizeHintRole?
                logger.warning("Performance work around: for tables with more than 1000 cells " +
                               "only the current column is resized and the others use that size.")
                horHeader.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
                self.tableView.resizeColumnToContents(oldCol)
                resizeAllSections(horHeader, self.tableView.columnWidth(oldCol))
        else:
            logger.debug("Setting horizontal resize mode to Interactive and reset header")
            horHeader.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
            resizeAllSections(horHeader, self.config.defaultColWidthCti.configValue)
            horHeader.reset()

        # Restore selection after select
        if selectionWasValid:
            newIndex = self.model.index(oldRow, oldCol)
            if newIndex.isValid():
                logger.debug("Restoring selection: row={}, col={}".format(oldRow, oldCol))
                self.tableView.setCurrentIndex(newIndex)
            else:
                logger.debug("Can't restore selection")



class TableInspectorModel(QtCore.QAbstractTableModel):
    """ Qt table model that gives access to the sliced array,
        To be used in the TableInspector.
    """
    def __init__(self, parent = None):
        """ Constructor

            :param separateFields: If True the fields of a structured array have their own
                                   separate cells.
            :param parent: parent Qt widget.
        """
        super(TableInspectorModel, self).__init__(parent)
        self._nRows = 0
        self._nCols = 0
        self._fieldNames = []
        self._slicedArray = None # can be a masked array or a regular numpy array
        self._rtiInfo = {}

        self._separateFields = True  # User config option
        self._separateFieldOrientation = None # To store which axis is currently separated
        self._numbersInHeader = True
        self._font = None # Default font

        # The following members are simple attributes, they can be changed independently
        self.encoding = 'utf-8'
        self.strFormat = None
        self.numFormat = None
        self.intFormat = None
        self.otherFormat = None
        self.maskFormat = None
        self.textAlignment = None
        self.verAlignment = None


    def updateState(self, slicedArray, rtiInfo, separateFields):
        """ Sets the slicedArray and rtiInfo and other members. This will reset the model.

            Will be called from the tableInspector._drawContents.
        """
        self.beginResetModel()
        try:
            # The sliced array can be a masked array or a (regular) numpy array.
            # The table works fine with masked arrays, no need to replace the masked values.
            self._slicedArray = slicedArray
            if slicedArray is None:
                self._nRows = 0
                self._nCols = 0
                self._fieldNames = []
            else:
                self._nRows, self._nCols = self._slicedArray.shape
                if self._slicedArray.data.dtype.names:
                    self._fieldNames = self._slicedArray.data.dtype.names
                else:
                    self._fieldNames = []

            self._rtiInfo = rtiInfo
            self._separateFields = separateFields

            # Don't put numbers in the header if the record is of structured type, fields are
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


    def _cellValue(self, index):
        """ Returns the data value of the cell at the index (without any string conversion)
        """
        row = index.row()
        col = index.column()
        if (row < 0 or row >= self.rowCount() or col < 0 or col >= self.columnCount()):
            return None

        # The check above should have returned None if the sliced array is None
        assert self._slicedArray is not None, "Sanity check failed."

        nFields = len(self._fieldNames)

        data = self._slicedArray.data
        if self._separateFieldOrientation == Qt.Horizontal:
            dataValue = data[row, col // nFields][self._fieldNames[col % nFields]]
        elif self._separateFieldOrientation == Qt.Vertical:
            dataValue = data[row // nFields, col][self._fieldNames[row % nFields]]
        else:
            dataValue = data[row, col]

        return dataValue


    def _cellMask(self, index):
        """ Returns the data mask of the cell at the index (without any string conversion)
        """
        row = index.row()
        col = index.column()
        if (row < 0 or row >= self.rowCount() or col < 0 or col >= self.columnCount()):
            return None

        # The check above should have returned None if the sliced array is None
        assert self._slicedArray is not None, "Sanity check failed."

        nFields = len(self._fieldNames)
        mask = self._slicedArray.mask
        if is_an_array(mask):
            if self._separateFieldOrientation == Qt.Horizontal:
                maskValue = mask[row, col // nFields][self._fieldNames[col % nFields]]
            elif self._separateFieldOrientation == Qt.Vertical:
                maskValue = mask[row // nFields, col][self._fieldNames[row % nFields]]
            else:
                maskValue = mask[row, col]
        else:
            maskValue = mask

        # Here maskValue can still be a list in case of structured arrays. It can even still be
        # a numpy array in case of a structured array with sub arrays as fields
        if is_an_array(maskValue):
            allMasked = np.all(maskValue)
        else:
            try:
                allMasked = all(maskValue)
            except TypeError as ex:
                allMasked = bool(maskValue)

        return allMasked


    def data(self, index, role = Qt.DisplayRole):
        """ Returns the data at an index for a certain role
        """
        try:
            if role == Qt.DisplayRole:
                return to_string(self._cellValue(index), masked=self._cellMask(index),
                                 decode_bytes=self.encoding, maskFormat=self.maskFormat,
                                 strFormat=self.strFormat, intFormat=self.intFormat,
                                 numFormat=self.numFormat, otherFormat=self.otherFormat)

            elif role == Qt.FontRole:
                #assert self._font, "Font undefined"
                return self._font

            elif role == Qt.TextColorRole:
                masked = self._cellMask(index)
                if not is_an_array(masked) and masked:
                    return self.missingColor
                else:
                    return self.dataColor

            elif role == Qt.TextAlignmentRole:
                if self.horAlignment == ALIGN_SMART:
                    cellContainsNumber = isinstance(self._cellValue(index), numbers.Number)
                    horAlign = Qt.AlignRight if cellContainsNumber else Qt.AlignLeft
                    return horAlign | self.verAlignment
                else:
                    return self.horAlignment | self.verAlignment

            else:
                return None
        except Exception as ex:
            logger.error("Slot is not exception-safe.")
            logger.exception(ex)
            if DEBUGGING:
                raise


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
