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

""" Collector Widget.
"""
from __future__ import print_function

import logging, os
import numpy as np
import numpy.ma as ma

from argos.collect.collectortree import CollectorTree, CollectorSpinBox
from argos.inspector.abstract import UpdateReason
from argos.qt import Qt, QtWidgets, QtGui, QtCore, QtSignal, QtSlot
from argos.repo.baserti import BaseRti
from argos.utils.cls import check_class, check_is_a_sequence, check_is_an_array, is_an_array
from argos.utils.masks import ArrayWithMask
from argos.widgets.constants import TOP_DOCK_HEIGHT, DOCK_SPACING, DOCK_MARGIN

logger = logging.getLogger(__name__)

FAKE_DIM_NAME = '-'     # The name of the fake dimension with length 1
FAKE_DIM_OFFSET = 1000  # Fake dimensions start here (so all arrays must have a smaller ndim)


# Qt classes have many ancestors
#pylint: disable=R0901



class Collector(QtWidgets.QWidget):
    """ Widget for collecting the selected data.
        Consists of a tree to collect the VisItems, plus some buttons to add or remove then.

        The CollectorTree only stores the VisItems, the intelligence is located in the Collector
        itself.
    """
    sigContentsChanged = QtSignal(str) # one of the UpdateReason values.

    def __init__(self, windowNumber):
        """ Constructor
        """
        super(Collector, self).__init__()

        self._windowNumber = windowNumber
        self._rti = None
        self._rtiInfo = None

        self._signalsBlocked = False
        self.COL_FIRST_COMBO = 1     # Column that contains the first (left most) combobox
        self.AXIS_POST_FIX = "-axis" # Added to the axis label to give the combox labels.
        self._axisNames = []         # Axis names. Correspond to the independent variables
        self._fullAxisNames = []       # Will be set in clearAndSetComboBoxes
        self._comboBoxes = []        # Will be set in clearAndSetComboBoxes
        self._spinBoxes = []         # Will be set in createSpinBoxes

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setSpacing(DOCK_SPACING)
        self.layout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)
        self.buttonLayout = QtWidgets.QVBoxLayout()
        # self.layout.setContentsMargins(2, 0, 2, 0)

        # Add tree
        self.tree = CollectorTree(self)
        self.layout.addWidget(self.tree)

        # Add buttons (not yet implemented)
        # self.addVisItemButton = QtWidgets.QPushButton("Add")
        # self.addVisItemButton.setEnabled(False) # not yet implemented
        # self.buttonLayout.addWidget(self.addVisItemButton, stretch=0)
        # self.removeVisItemButton = QtWidgets.QPushButton("Remove")
        # self.removeVisItemButton.setEnabled(False) # not yet implemented
        # self.buttonLayout.addWidget(self.removeVisItemButton, stretch=0)
        # self.buttonLayout.addStretch(stretch=1)
        # self.layout.addLayout(self.buttonLayout, stretch=0)

        self._updateRtiInfo()


    def sizeHint(self):
        """ The recommended size for the widget."""
        return QtCore.QSize(300, TOP_DOCK_HEIGHT)

    @property
    def windowNumber(self):
        """ The instance number of the window this collector belongs to.
        """
        return self._windowNumber

    @property
    def rti(self):
        """ The current repository tree item. Can be None.
        """
        return self._rti


    @property
    def rtiIsSliceable(self):
        """ Returns true if the RTI is not None and is sliceable
        """
        return self._rti and self._rti.isSliceable


    @property
    def axisNames(self):
        """ Returns a the axis names.
            The axis names indicate the independent dimensions of the visualization.
        """
        return self._axisNames


    @property
    def fullAxisNames(self):
        """ Returns the of the combobox labels.
            The combobox labes the axisNames followed by '-axis'
        """
        return self._fullAxisNames


    @property
    def maxCombos(self):
        """ Returns the maximum number of combo boxes """
        return len(self._fullAxisNames)


    # @property
    # def numCombos(self):
    #     """ Returns the number of combo boxes """
    #     return len(self._comboBoxes)


    def blockChildrenSignals(self, block):
        """ If block equals True, the signals of the combo boxes and spin boxes are blocked
            Returns the old blocking state.
        """
        logger.debug("Blocking collector signals")
        for spinBox in self._spinBoxes:
            spinBox.blockSignals(block)
        for comboBox in self._comboBoxes:
            comboBox.blockSignals(block)
        result = self._signalsBlocked
        self._signalsBlocked = block
        return result


    def _setColumnCountForContents(self):
        """ Sets the column count given the current axes and selected RTI.
            Returns the newly set column count.
        """
        numRtiDims = self.rti.nDims if self.rti and self.rti.isSliceable else 0

        colCount = self.COL_FIRST_COMBO + max(numRtiDims, len(self.axisNames))
        self.tree.model().setColumnCount(colCount)
        return colCount


    def clear(self):
        """ Removes all VisItems
        """
        model = self.tree.model()
        # Don't use model.clear(). it will delete the column sizes
        model.removeRows(0, 1)
        model.setRowCount(1)
        self._setColumnCountForContents()


    def clearAndSetComboBoxes(self, axesNames):
        """ Removes all comboboxes.
        """
        logger.debug("Collector clearAndSetComboBoxes: {}".format(axesNames))
        check_is_a_sequence(axesNames)
        row = 0
        self._deleteComboBoxes(row)
        self.clear()
        self._setAxesNames(axesNames)
        self._createComboBoxes(row)
        self._updateWidgets()


    def _setAxesNames(self, axisNames):
        """ Sets the axesnames, combobox lables and updates the headers. Removes old values first.
            The comboLables is the axes name + '-axis'
        """
        for col, _ in enumerate(self._fullAxisNames, self.COL_FIRST_COMBO):
            self._setHeaderLabel(col, '')

        self._axisNames = tuple(axisNames)
        self._fullAxisNames = tuple([axName + self.AXIS_POST_FIX for axName in axisNames])

        for col, label in enumerate(self._fullAxisNames, self.COL_FIRST_COMBO):
            self._setHeaderLabel(col, label)


    def _setHeaderLabel(self, col, text):
        """ Sets the header of column col to text.
            Will increase the number of columns if col is larger than the current number.
        """
        model = self.tree.model()
        item = model.horizontalHeaderItem(col)
        if item:
            item.setText(text)
        else:
            model.setHorizontalHeaderItem(col, QtGui.QStandardItem(text))


    @QtSlot(BaseRti)
    def setRti(self, rti):
        """ Updates the current VisItem from the contents of the repo tree item.

            Is a slot but the signal is usually connected to the Collector, which then calls
            this function directly.
        """
        check_class(rti, BaseRti)
        #assert rti.isSliceable, "RTI must be sliceable" # TODO: maybe later

        self._rti = rti
        self._updateWidgets()
        self._updateRtiInfo()


    def _updateWidgets(self):
        """ Updates the combo and spin boxes given the new rti or axes.
            Emits the sigContentsChanged signal.
        """
        row = 0
        model = self.tree.model()

        # Create path label
        nodePath = '' if self.rti is None else self.rti.nodePath
        pathItem = QtGui.QStandardItem(nodePath)
        pathItem.setToolTip(nodePath)
        pathItem.setEditable(False)
        if self.rti is not None:
            pathItem.setIcon(self.rti.decoration)
        model.setItem(row, 0, pathItem)

        self._deleteSpinBoxes(row)
        self._populateComboBoxes(row)
        self._createSpinBoxes(row)
        self._updateRtiInfo()

        self.tree.resizeColumnsToContents(startCol=self.COL_FIRST_COMBO)

        logger.debug("{} sigContentsChanged signal (_updateWidgets)"
                      .format("Blocked" if self.signalsBlocked() else "Emitting"))
        self.sigContentsChanged.emit(UpdateReason.RTI_CHANGED)


    def _createComboBoxes(self, row):
        """ Creates a combo box for each of the fullAxisNames
        """
        tree = self.tree
        model = self.tree.model()
        self._setColumnCountForContents()

        for col, _ in enumerate(self._axisNames, self.COL_FIRST_COMBO):
            logger.debug("Adding combobox at ({}, {})".format(row, col))
            comboBox = QtWidgets.QComboBox()
            comboBox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
            comboBox.activated.connect(self._comboBoxActivated)
            self._comboBoxes.append(comboBox)

            #editor = LabeledWidget(QtWidgets.QLabel(comboLabel), comboBox)
            tree.setIndexWidget(model.index(row, col), comboBox)


    def _deleteComboBoxes(self, row):
        """ Deletes all comboboxes of a row
        """
        tree = self.tree
        model = self.tree.model()

        for col in range(self.COL_FIRST_COMBO, self.maxCombos):
            logger.debug("Removing combobox at: ({}, {})".format(row, col))
            tree.setIndexWidget(model.index(row, col), None)

        self._comboBoxes = []


    # TODO: why again don't we create the comboxes when a new RTI is selected (just like the spins)?
    def _populateComboBoxes(self, row):
        """ Populates the combo boxes with values of the repo tree item
        """
        logger.debug("_populateComboBoxes")
        for comboBox in self._comboBoxes:
            comboBox.clear()

        if not self.rtiIsSliceable:
            # Add an empty item to the combo boxes so that resize to contents works.
            for comboBoxNr, comboBox in enumerate(self._comboBoxes):
                comboBox.addItem('', userData=None)
                comboBox.setEnabled(False)
            return

        nDims = self._rti.nDims
        nCombos = len(self._comboBoxes)

        for comboBoxNr, comboBox in enumerate(self._comboBoxes):
            # Add a fake dimension of length 1
            comboBox.addItem(FAKE_DIM_NAME, userData = FAKE_DIM_OFFSET + comboBoxNr)

            for dimNr in range(nDims):
                comboBox.addItem(self._rti.dimensionNames[dimNr], userData=dimNr)

            # Set combobox current index
            if nDims >= nCombos:
                # We set the nth combo-box index to the last item - n. This because the
                # NetCDF-CF conventions have the preferred dimension order of T, Z, Y, X.
                # The +1 below is from the fake dimension.
                curIdx = nDims + 1 - nCombos + comboBoxNr
            else:
                # If there are less dimensions in the RTI than the inspector can show, we fill
                # the comboboxes starting at the leftmost and set the remaining comboboxes to the
                # fake dimension. This means that a table inspector fill have one column and many
                # rows, which is the most convenient.
                curIdx = comboBoxNr + 1 if comboBoxNr < nDims else 0

            assert 0 <= curIdx <= nDims + 1, \
                "curIdx should be <= {}, got {}".format(nDims + 1, curIdx)

            comboBox.setCurrentIndex(curIdx)
            comboBox.setEnabled(True)
            #comboBox.adjustSize() # necessary?


    # def getComboBoxDimensionName(self, comboBoxNr):
    #     """ Returns the currently selected dimension index of combo box nr comboBoxNr
    #     """
    #     self._comboBoxes[comboBoxNr].currentText()
    #
    #
    # def getComboBoxDimensionIndex(self, comboBoxNr):
    #     """ Returns the currently selected dimension index of combo box nr comboBoxNr
    #     """
    #     return self._comboBoxDimensionIndex(self._comboBoxes[comboBoxNr])


    def _comboBoxDimensionIndex(self, comboBox):
        """ Returns the dimension index (from the user data) of the current item of the combo box.
        """
        return comboBox.itemData(comboBox.currentIndex())


    def _dimensionSelectedInComboBox(self, dimNr):
        """ Returns True if the dimension is selected in one of the combo boxes.
        """
        for combobox in self._comboBoxes:
            if self._comboBoxDimensionIndex(combobox) == dimNr:
                return True
        return False


    def _createSpinBoxes(self, row):
        """ Creates a spinBox for each dimension that is not selected in a combo box.
        """
        assert len(self._spinBoxes) == 0, "Spinbox list not empty. Call _deleteSpinBoxes first"

        if not self.rtiIsSliceable:
            return

        logger.debug("_createSpinBoxes, array shape: {}".format(self._rti.arrayShape))

        self._setColumnCountForContents()

        tree = self.tree
        model = self.tree.model()
        col = self.COL_FIRST_COMBO + self.maxCombos

        for dimNr, dimSize in enumerate(self._rti.arrayShape):

            if self._dimensionSelectedInComboBox(dimNr):
                continue

            self._setHeaderLabel(col, '')

            spinBox = CollectorSpinBox()
            self._spinBoxes.append(spinBox)

            spinBox.setKeyboardTracking(False)
            spinBox.setCorrectionMode(QtWidgets.QAbstractSpinBox.CorrectToNearestValue)

            spinBox.setMinimum(0)
            spinBox.setMaximum(dimSize - 1)
            spinBox.setSingleStep(1)
            spinBox.setValue(dimSize // 2) # select the middle of the slice
            spinBox.setPrefix("{}: ".format(self._rti.dimensionNames[dimNr]))
            spinBox.setSuffix("/{}".format(spinBox.maximum()))
            spinBox.setProperty("dim_nr", dimNr)
            #spinBox.adjustSize() # necessary?

            # This must be done after setValue to prevent emitting too many signals
            spinBox.valueChanged[int].connect(self._spinboxValueChanged)

            tree.setIndexWidget(model.index(row, col), spinBox)
            col += 1

        # Resize the spinbox columns to their new contents
        self.tree.resizeColumnsToContents(startCol=self.COL_FIRST_COMBO + self.maxCombos)


    def _deleteSpinBoxes(self, row):
        """ Removes all spinboxes
        """
        tree = self.tree
        model = self.tree.model()

        for col, spinBox in enumerate(self._spinBoxes, self.COL_FIRST_COMBO + self.maxCombos):
            spinBox.valueChanged[int].disconnect(self._spinboxValueChanged)
            tree.setIndexWidget(model.index(row, col), None)
        self._spinBoxes = []

        self._setColumnCountForContents()


    @QtSlot(int)
    def _comboBoxActivated(self, index, comboBox=None):
        """ Is called when a combo box value was changed by the user.

            Updates the spin boxes and sets other combo boxes having the same index to
            the fake dimension of length 1.
        """
        if comboBox is None:
            comboBox = self.sender()
        assert comboBox, "comboBox not defined and not the sender"

        blocked = self.blockChildrenSignals(True)

        # If one of the other combo boxes has the same value, set it to the fake dimension
        curDimIdx = self._comboBoxDimensionIndex(comboBox)
        if curDimIdx < FAKE_DIM_OFFSET:
            otherComboBoxes = [cb for cb in self._comboBoxes if cb is not comboBox]
            for otherComboBox in otherComboBoxes:
                if otherComboBox.currentIndex() == comboBox.currentIndex():
                    #newIdx = otherComboBox.findData(FAKE_DIM_IDX)
                    #otherComboBox.setCurrentIndex(newIdx)
                    otherComboBox.setCurrentIndex(0) # Fake dimension is always the first

        # Show only spin boxes that are not selected
        row = 0
        self._deleteSpinBoxes(row)
        self._createSpinBoxes(row)
        self._updateRtiInfo()

        self.blockChildrenSignals(blocked)

        logger.debug("{} sigContentsChanged signal (comboBox)"
                      .format("Blocked" if self.signalsBlocked() else "Emitting"))
        self.sigContentsChanged.emit(UpdateReason.COLLECTOR_COMBO_BOX)


    @QtSlot(int)
    def _spinboxValueChanged(self, index, spinBox=None):
        """ Is called when a spin box value was changed.

            Updates the spin boxes and sets other combo boxes having the same index to
            the fake dimension of length 1.
        """
        if spinBox is None:
            spinBox = self.sender()
        assert spinBox, "spinBox not defined and not the sender"

        logger.debug("{} sigContentsChanged signal (spinBox)"
                      .format("Blocked" if self.signalsBlocked() else "Emitting"))
        self.sigContentsChanged.emit(UpdateReason.COLLECTOR_SPIN_BOX)


    def getSlicedArray(self, copy=True):
        """ Slice the rti using a tuple of slices made from the values of the combo and spin boxes.

            :param copy: If True (the default), a copy is made so that inspectors cannot
                accidentally modify the underlying of the RTIs. You can set copy=False as a
                potential optimization, but only if you are absolutely sure that you don't modify
                the the slicedArray in your inspector! Note that this function calls transpose,
                which can still make a copy of the array for certain permutations.

            :return: Numpy masked array with the same number of dimension as the number of
                comboboxes (this can be zero!).

                Returns None if no slice can be made (i.e. the RTI is not sliceable).
        """
        #logger.debug("getSlicedArray() called")

        if not self.rtiIsSliceable:
            return None

        # The dimensions that are selected in the combo boxes will be set to slice(None),
        # the values from the spin boxes will be set as a single integer value
        nDims = self.rti.nDims
        sliceList = [slice(None)] * nDims

        for spinBox in self._spinBoxes:
            dimNr = spinBox.property("dim_nr")
            sliceList[dimNr] = spinBox.value()

        # Make the array slicer. It needs to be a tuple, a list of only integers will be
        # interpreted as an index. With a tuple, array[(exp1, exp2, ..., expN)] is equivalent to
        # array[exp1, exp2, ..., expN].
        # See: http://docs.scipy.org/doc/numpy/reference/arrays.indexing.html
        logger.debug("Array slice list: {}".format(str(sliceList)))
        slicedArray = self.rti[tuple(sliceList)]

        # Make a copy to prevent inspectors from modifying the underlying array.
        if copy:
            slicedArray = ma.copy(slicedArray)

        # If there are no comboboxes the sliceList will contain no Slices objects, only ints. Then
        # the resulting slicedArray will be a usually a scalar (only structured fields may yield an
        # array). We convert this scalar to a zero-dimensional Numpy array so that inspectors
        # always get an array (having the same number of dimensions as the dimensionality of the
        # inspector, i.e. the number of comboboxes).
        if self.maxCombos == 0:
            slicedArray = ma.MaskedArray(slicedArray)

        # Post-condition type check
        check_is_an_array(slicedArray, np.ndarray)

        # Enforce the return type to be a masked array.
        if not isinstance(slicedArray, ma.MaskedArray):
            slicedArray = ma.MaskedArray(slicedArray)

        # Add fake dimensions of length 1 so that result.ndim will equal the number of combo boxes
        for dimNr in range(slicedArray.ndim, self.maxCombos):
            #logger.debug("Adding fake dimension: {}".format(dimNr))
            slicedArray = ma.expand_dims(slicedArray, dimNr)

        # Post-condition dimension check
        assert slicedArray.ndim == self.maxCombos, \
            "Bug: getSlicedArray should return a {:d}D array, got: {}D" \
            .format(self.maxCombos, slicedArray.ndim)

        # Convert to ArrayWithMask class for working around issues with the numpy maskedarray
        awm = ArrayWithMask.createFromMaskedArray(slicedArray)
        del slicedArray

        # Shuffle the dimensions to be in the order as specified by the combo boxes
        comboDims = [self._comboBoxDimensionIndex(cb) for cb in self._comboBoxes]
        permutations = np.argsort(comboDims)
        logger.debug("slicedArray.shape: {}".format(awm.data.shape))
        logger.debug("Transposing dimensions: {}".format(permutations))
        awm = awm.transpose(permutations)

        awm.checkIsConsistent()

        return awm


    def getSlicesString(self):
        """ Returns a string representation of the slices that are used to get the sliced array.
            For example returns '[:, 5]' if the combo box selects dimension 0 and the spin box 5.
        """
        if not self.rtiIsSliceable:
            return ''

        # The dimensions that are selected in the combo boxes will be set to slice(None),
        # the values from the spin boxes will be set as a single integer value
        nDims = self.rti.nDims
        sliceList = [':'] * nDims

        for spinBox in self._spinBoxes:
            dimNr = spinBox.property("dim_nr")
            sliceList[dimNr] = str(spinBox.value())

        # No need to shuffle combobox dimensions like in getSlicedArray; all combobox dimensions
        # yield a colon.

        return "[" + ", ".join(sliceList) + "]"


    # def independentDimensionNames(self):
    #     """ Returns list of the names of the independent dimensions, which have been selected in
    #         the combo boxes.
    #     """
    #     return [combobox.currentText() for combobox in self._comboBoxes]
    #
    #
    # def independentDimensionUnits(self):
    #     """ Returns list of the units of the independent dimensions, which have been selected in
    #         the combo boxes. At the moment return '' for each independent dimension.
    #     """
    #     return ['' for _combobox in self._comboBoxes]
    #
    #
    # def dependentDimensionName(self):
    #     """ Returns the name of the dependent dimension.
    #         A good default is the name of the RTI.
    #     """
    #     return self.rti.nodeName if self.rti else ''


    @property
    def rtiInfo(self):
        """ Returns a dictionary with information on the selected RTI (repo tree item).
            This can be used in string formatting of config options. For instance: the plot title
            can be specified as: '{path} {slices}', which will be expanded with the actual nodePath
            and slices-string of the RTI.

            If no RTI is selected the applicable values will be empty strings.

            The dictionary has the following contents:
                slices : a string representation of the selected slice indices.
                name        : nodeName of the RTI
                path        : nodePath of the RTI
                unit        : unit of the RTI in parentheses
                raw-unit    : unit of the RTI without parentheses (empty string if no unit given)
                n-dim       : dimension selected in the combobox for axis n. The axis name will be
                              in lower case (so e.g. x-dim, y-dim, etc)
        """
        return self._rtiInfo


    def _updateRtiInfo(self):
        """ Updates the _rtiInfo property when a new RTI is set or the comboboxes value change.
        """
        logger.debug("Updating self._rtiInfo")
        # Info about the dependent dimension
        rti = self.rti
        if rti is None:
            info = {'slices': '',
                    'name': '',
                    'path': '',
                    'file-name': '',
                    'dir-name': '',
                    'base-name': '',
                    'unit': '',
                    'raw-unit': ''}
        else:
            dirName, baseName = os.path.split(rti.fileName)
            info = {'slices': self.getSlicesString(),
                    'name': rti.nodeName,
                    'path': rti.nodePath,
                    'file-name': rti.fileName,
                    'dir-name': dirName,
                    'base-name': baseName,
                    'unit': '({})'.format(rti.unit) if rti.unit else '',
                    'raw-unit': rti.unit}

        # Add the info of the independent dimensions (appended with the axis name of that dim).
        for axisName, comboBox in zip(self._axisNames, self._comboBoxes):
            dimName = comboBox.currentText()
            key = '{}-dim'.format(axisName.lower())
            info[key] = dimName

        self._rtiInfo = info

