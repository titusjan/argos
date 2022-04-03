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

""" Collector Tree.
"""
from __future__ import print_function

import logging
import warnings

import numpy as np

from argos.info import DEBUGGING
from argos.qt import Qt, QtCore, QtGui, QtWidgets, QtSlot
from argos.qt.togglecolumn import ToggleColumnTreeView
from argos.widgets.constants import COLLECTOR_TREE_ICON_SIZE
from argos.utils.cls import check_class

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901

class CollectorTree(ToggleColumnTreeView):
    """ Tree widget for collecting the selected data. Includes an internal tree model.

        NOTE: this class is not meant to be used directly but is 'private' to the Collector().
        That is, plugins should interact with the Collector class, not the CollectorTree()
    """

    def __init__(self, parent):
        """ Constructor
        """
        super(CollectorTree, self).__init__(parent=parent)

        self._comboLabels = None

        nCols = 1
        model = QtGui.QStandardItemModel(3, nCols)
        self.setModel(model)
        self.setTextElideMode(Qt.ElideMiddle) # ellipsis appear in the middle of the text

        self.setRootIsDecorated(False) # disable expand/collapse triangle
        self.setUniformRowHeights(True)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setAnimated(True)
        self.setAllColumnsShowFocus(True)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.setIconSize(COLLECTOR_TREE_ICON_SIZE)

        treeHeader = self.header()
        treeHeader.setStretchLastSection(False)
        treeHeader.setSectionsMovable(False)

        treeHeader.resizeSection(0, 600) # For item path
        treeHeader.setSectionResizeMode(QtWidgets.QHeaderView.Interactive) # don't set to stretch

        labels = [''] * model.columnCount()
        labels[0] = "Path"
        model.setHorizontalHeaderLabels(labels)

        #enabled = dict((name, False) for name in self.HEADERS)
        #checked = dict((name, True) for name in self.HEADERS)
        #self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})


    def resizeColumnsFromContents(self, startCol=None):
        """ Resize columns depending on their contents.

            The width of the first column (showing the path) will not be changed
            The columns containing combo boxes will be set to the size hints of these combo boxes
            The remaining width (if any) is devided over the spin boxes.
        """
        logger.debug("resizeColumnsFromContents called.")
        numCols = self.model().columnCount()
        startCol = 0 if startCol is None else max(startCol, 0)

        # Set columns with comboboxes to their size hints
        row = 0
        header = self.header()
        for col in range(startCol, numCols):
            indexWidget = self.indexWidget(self.model().index(row, col))
            if indexWidget:
                if isinstance(indexWidget, QtWidgets.QComboBox):
                    header.resizeSection(col, indexWidget.sizeHint().width())

        # Collect size hints of spin boxes and indices of all other columns.
        indexSpin = []
        indexNonSpin = []
        spinBoxSizeHints = []
        spinBoxMaximums = []
        for col in range(0, numCols):
            indexWidget = self.indexWidget(self.model().index(row, col))
            if indexWidget and isinstance(indexWidget, (QtWidgets.QSpinBox, SpinSlider)):
                spinBoxSizeHints.append(indexWidget.spinbox.sizeHint().width())
                spinBoxMaximums.append(max(0, indexWidget.spinbox.maximum())) # prevent negatives
                indexSpin.append(col)
            else:
                indexNonSpin.append(col)

        if len(indexSpin) == 0:
            return

        headerWidth = self.header().width()
        spinBoxSizeHints = np.array(spinBoxSizeHints)
        spinBoxTotalSizeHints = np.sum(np.array(spinBoxSizeHints))
        colWidths = np.array([self.header().sectionSize(idx) for idx in range(numCols)])
        nonSpinBoxTotalWidth = np.sum(colWidths[indexNonSpin])
        remainingTotal = max(0, headerWidth - nonSpinBoxTotalWidth - spinBoxTotalSizeHints)

        with warnings.catch_warnings():
            # Ignore divide by zero warnings when all elements have the same value
            warnings.simplefilter("ignore")
            spinBoxWeights = np.maximum(0.5, np.log10(np.array(spinBoxMaximums)))
            normSpinBoxWeights = spinBoxWeights / np.sum(spinBoxWeights)
            extraWidthPerSpinBox = remainingTotal * normSpinBoxWeights
            newSpinBoxWidths = spinBoxSizeHints + extraWidthPerSpinBox

        if DEBUGGING:  # Only during debugging to reduce devops log file size.
            logger.debug("Dividing the remaining width over the spinboxes.")
            logger.debug("Header width               : {}".format(headerWidth))
            logger.debug("Column widths              : {}".format(colWidths))
            logger.debug("Width of non-spinboxes     : {}".format(nonSpinBoxTotalWidth))
            logger.debug("Total size hint spinboxes  : {}".format(spinBoxTotalSizeHints))
            logger.debug("Remaining width to divide  : {}".format(remainingTotal))
            logger.debug("Spinbox maximums           : {}".format(spinBoxMaximums))
            logger.debug("Normalized spinbox weights : {}".format(normSpinBoxWeights))
            logger.debug("Extra width per spin box   : {}".format(extraWidthPerSpinBox))
            logger.debug("New spinbox widths         : {}".format(newSpinBoxWidths))

        # Divide the remaining width over the spin boxes using the log(nrElements) as weights.
        # If the remaining total is less than zero, just set the widths to the size hints (a
        # horizontal scrollbar will appear).
        for idx, newWidth in zip(indexSpin, newSpinBoxWidths):
            header.resizeSection(idx, round(newWidth))



class CollectorSpinBox(QtWidgets.QSpinBox):
    """ A spinbox for use in the collector.
        Overrides the sizeHint so that is not truncated when large dimension names are selected
    """
    def __init__(self, *args, **kwargs):
        """ Constructor
        """
        super(CollectorSpinBox, self).__init__(*args, **kwargs)
        self._cachedSizeHint = None


    def sizeHint(self):
        """ Reimplemented from the C++ Qt source of QAbstractSpinBox.sizeHint, but without
            truncating to a maximum of 18 characters.
        """
        # The cache is invalid after the prefix, postfix and other properties
        # have been set. I disabled it because sizeHint isn't called that often.
        #if self._cachedSizeHint is not None:
        #    return self._cachedSizeHint

        orgSizeHint = super(CollectorSpinBox, self).sizeHint()

        self.ensurePolished()
        fm = QtGui.QFontMetrics(self.fontMetrics())

        # This was h = d.edit.sizeHint().height(), but that didn't work. In the end we set the
        # height to the height calculated from the parent.
        h = orgSizeHint.height()
        w = 0

        # QLatin1Char seems not to be implemented.
        # Using regular string literals and hope for the best
        s = self.prefix() + self.textFromValue(self.minimum()) + self.suffix() #+ ' '

        # We disabled truncating the string here!!
        #s = s[:18]
        w = max(w, fm.width(s))

        s = self.prefix() + self.textFromValue(self.maximum()) + self.suffix() #+ ' '

        # We disabled truncating the string here!!
        #s = s[:18]
        w = max(w, fm.width(s))
        if len(self.specialValueText()):
            s = self.specialValueText()
            w = max(w, fm.width(s))

        w += 2 # cursor blinking space

        w -= 15 # The spinboxes seemed to wide. Made a bit smaller by Pepijn.

        opt = QtWidgets.QStyleOptionSpinBox()
        self.initStyleOption(opt)
        hint = QtCore.QSize(w, h)
        extra = QtCore.QSize(35, 6)

        opt.rect.setSize(hint + extra)
        extra += hint - self.style().subControlRect(
            QtWidgets.QStyle.CC_SpinBox, opt, QtWidgets.QStyle.SC_SpinBoxEditField, self).size()

        # get closer to final result by repeating the calculation
        opt.rect.setSize(hint + extra)
        extra += hint - self.style().subControlRect(
            QtWidgets.QStyle.CC_SpinBox, opt, QtWidgets.QStyle.SC_SpinBoxEditField, self).size()
        hint += extra

        opt.rect = self.rect()
        result = (self.style().sizeFromContents(QtWidgets.QStyle.CT_SpinBox, opt, hint, self)
                  .expandedTo(QtWidgets.QApplication.globalStrut()))
        self._cachedSizeHint = result

        # Use the height ancestor's sizeHint
        result.setHeight(orgSizeHint.height())

        return result


class SpinSlider(QtWidgets.QWidget):
    """ A SpinBox and Slider widgets next to each other.

        The layout will be created. It can be accessed as self.layout
    """
    #sigValueChanged = QtSignal(int)

    def __init__(self,
                 spinBox,
                 slider = None,
                 layoutSpacing = None,
                 layoutContentsMargins = (0, 0, 0, 0),
                 parent=None):
        """ Constructor.

            The settings (min, max, enabled, etc) from the SpinBox will be used for the slider
            as well. That is, the spin box is the master.
        """
        super(SpinSlider, self).__init__(parent=parent)

        check_class(spinBox, QtWidgets.QSpinBox, allow_none=True)
        check_class(slider, QtWidgets.QSlider, allow_none=True)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(*layoutContentsMargins)
        if layoutSpacing is not None:
            self.layout.setSpacing(layoutSpacing)

        if spinBox is None:
            self.spinbox = QtWidgets.QSpinBox()
        else:
            self.spinbox = spinBox

        if slider is None:
            self.slider = QtWidgets.QSlider(Qt.Horizontal)
        else:
            self.slider = slider

        self.slider.setMinimum(self.spinbox.minimum())
        self.slider.setMaximum(self.spinbox.maximum())
        self.slider.setValue(self.spinbox.value())
        self.slider.setEnabled(self.spinbox.isEnabled())

        self.layout.addWidget(self.spinbox, stretch=0)
        self.layout.addWidget(self.slider, stretch=1)

        self.spinbox.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self.spinbox.setValue)
