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

from argos.qt import Qt, QtCore, QtGui, QtWidgets, QtSlot
from argos.qt.togglecolumn import ToggleColumnTreeView
from argos.widgets.constants import COLLECTOR_TREE_ICON_SIZE

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901

#TODO: do we still need this as a separate class?
class CollectorTree(ToggleColumnTreeView):
    """ Tree widget for collecting the selected data. Includes an internal tree model.

        NOTE: this class is not meant to be used directly but is 'private' to the Collector().
        That is, plugins should interact with the Collector class, not the CollectorTree()
    """
    HEADERS = ["item path", "item name"] # TODO: this can't be right. Is this even used?
    (COL_ITEM_PATH, COL_ITEM_NAME) = range(len(HEADERS))


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
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setAnimated(True)
        self.setAllColumnsShowFocus(True)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.setIconSize(COLLECTOR_TREE_ICON_SIZE)

        treeHeader = self.header()
        treeHeader.setStretchLastSection(False)
        treeHeader.setSectionsMovable(False)

        treeHeader.resizeSection(0, 400) # For item path
        treeHeader.setSectionResizeMode(QtWidgets.QHeaderView.Interactive) # don't set to stretch

        labels = [''] * model.columnCount()
        labels[0] = "path"
        model.setHorizontalHeaderLabels(labels)

        #enabled = dict((name, False) for name in self.HEADERS)
        #checked = dict((name, True) for name in self.HEADERS)
        #self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})


    def resizeColumnsToContents(self, startCol=None, stopCol=None):
        """ Resizes all columns to the contents
        """
        numCols = self.model().columnCount()
        startCol = 0 if startCol is None else max(startCol, 0)
        stopCol  = numCols if stopCol is None else min(stopCol, numCols)

        row = 0
        for col in range(startCol, stopCol):
            indexWidget = self.indexWidget(self.model().index(row, col))

            if indexWidget:
                contentsWidth = indexWidget.sizeHint().width()
            else:
                contentsWidth = self.header().sectionSizeHint(col)

            self.header().resizeSection(col, contentsWidth)



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
        d = self
        fm = QtGui.QFontMetrics(self.fontMetrics())

        # This was h = d.edit.sizeHint().height(), but that didn't work. In the end we set the
        # height to the height calculated from the parent.
        h = orgSizeHint.height()
        w = 0

        # QLatin1Char seems not to be implemented.
        # Using regular string literals and hope for the best
        s = d.prefix() + d.textFromValue(d.minimum()) + d.suffix() + ' '

        # We disabled truncating the string here!!
        #s = s[:18]
        w = max(w, fm.width(s))

        s = d.prefix() + d.textFromValue(d.maximum()) + d.suffix() + ' '

        # We disabled truncating the string here!!
        #s = s[:18]
        w = max(w, fm.width(s))
        if len(d.specialValueText()):
            s = d.specialValueText()
            w = max(w, fm.width(s))

        w += 2 # cursor blinking space

        opt = QtWidgets.QStyleOptionSpinBox()
        self.initStyleOption(opt)
        hint = QtCore.QSize(w, h)
        extra = QtCore.QSize(35, 6)

        opt.rect.setSize(hint + extra)
        extra += hint - self.style().subControlRect(QtWidgets.QStyle.CC_SpinBox, opt,
                                                    QtWidgets.QStyle.SC_SpinBoxEditField, self).size()

        # get closer to final result by repeating the calculation
        opt.rect.setSize(hint + extra)
        extra += hint - self.style().subControlRect(QtWidgets.QStyle.CC_SpinBox, opt,
                                                    QtWidgets.QStyle.SC_SpinBoxEditField, self).size()
        hint += extra

        opt.rect = self.rect()
        result = (self.style().sizeFromContents(QtWidgets.QStyle.CT_SpinBox, opt, hint, self)
                  .expandedTo(QtWidgets.QApplication.globalStrut()))
        self._cachedSizeHint = result

        # Use the height ancestor's sizeHint
        result.setHeight(orgSizeHint.height())

        return result


