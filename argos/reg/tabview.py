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


""" Editable table for data store
"""

import logging
import os.path

from argos.utils.cls import type_name, check_class

from argos.info import icons_directory
from argos.reg.tabmodel import BaseTableModel
from argos.qt import QtCore, QtGui, QtWidgets, Qt
from argos.qt.togglecolumn import ToggleColumnTableView


logger = logging.getLogger(__name__)


class BaseTableView(ToggleColumnTableView):
    """ Editable QTableView that shows the contents of a BaseTableModel.
    """
    def __init__(self, model=None, parent=None):
        """ Constructor

            :param BaseTableModelmodel: a RegistryTableModel that maps the regItems
            :param QWidget parent: the parent widget
        """
        super(BaseTableView, self).__init__(parent)

        check_class(model, BaseTableModel)
        self.setModel(model)

        self.setTextElideMode(QtCore.Qt.ElideMiddle) # Does not work nicely when editing cells.
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSortingEnabled(False)
        self.setTabKeyNavigation(False)
        self.setWordWrap(False)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        Qiv = QtWidgets.QAbstractItemView
        #self.setEditTriggers(Qiv.DoubleClicked | Qiv.SelectedClicked | Qiv.EditKeyPressed)
        self.setEditTriggers(Qiv.NoEditTriggers)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

        self.verHeader = self.verticalHeader()
        self.verHeader.setSectionsMovable(False)
        self.verHeader.hide()

        self.horHeader = self.horizontalHeader()
        self.horHeader.setDefaultAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.horHeader.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.horHeader.setStretchLastSection(False)

        for col, canStretch in enumerate(model.store.canStretchPerColumn):
            if canStretch:
                self.horHeader.setSectionResizeMode(col, QtWidgets.QHeaderView.Stretch)
            else:
                self.horHeader.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)


    def getCurrentItem(self):
        """ Returns the item of the selected row, or None if none is selected
        """
        curIdx = self.currentIndex()
        return self.model().itemFromIndex(curIdx)


    def setCurrentCell(self, row, col=0):
        """ Sets the current row and column.
        """
        cellIdx = self.model().index(row, col)
        if not cellIdx.isValid():
            logger.warning("Can't set (row = {}, col = {}) in table".format(row, col))
        else:
            logger.debug("Setting cellIdx (row = {}, col = {}) in table".format(row, col))
        self.setCurrentIndex(cellIdx)



class TableEditWidget(QtWidgets.QWidget):
    """ Widget that contains a table plus buttons to update it

    """
    def __init__(self, tableModel=None, parent=None):
        """ Constructor.
        """
        super(TableEditWidget, self).__init__(parent=parent)

        self.setFocusPolicy(Qt.NoFocus)

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.mainLayout)

        self.tableView = BaseTableView(tableModel)
        self.mainLayout.addWidget(self.tableView)

        buttonLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addLayout(buttonLayout)

        iconDir = icons_directory()
        iconSize = QtCore.QSize(20, 20)

        self.addButton = QtWidgets.QPushButton()
        self.addButton.setToolTip("Add new row.")
        self.addButton.setIcon(QtGui.QIcon(os.path.join(iconDir, 'plus-sign-l.svg')))
        self.addButton.setIconSize(iconSize)
        self.addButton.clicked.connect(self.addRow)
        buttonLayout.addWidget(self.addButton)

        self.removeButton = QtWidgets.QPushButton()
        self.removeButton.setToolTip("Remove row.")
        self.removeButton.setIcon(QtGui.QIcon(os.path.join(iconDir, 'minus-sign-l.svg')))
        self.removeButton.setIconSize(iconSize)
        self.removeButton.clicked.connect(self.removeRow)
        buttonLayout.addWidget(self.removeButton)
        buttonLayout.addSpacing(25)

        self.moveUpButton = QtWidgets.QPushButton()
        self.moveUpButton.setToolTip("Move row up")
        self.moveUpButton.setIcon(QtGui.QIcon(os.path.join(iconDir, 'circle-arrow-up-l.svg')))
        self.moveUpButton.setIconSize(iconSize)
        self.moveUpButton.clicked.connect(lambda: self.moveRow(-1))
        buttonLayout.addWidget(self.moveUpButton)

        self.moveDownButton = QtWidgets.QPushButton()
        self.moveDownButton.setToolTip("Move row down")
        self.moveDownButton.setIcon(QtGui.QIcon(os.path.join(iconDir, 'circle-arrow-down-l.svg')))
        self.moveDownButton.setIconSize(iconSize)
        self.moveDownButton.clicked.connect(lambda: self.moveRow(+1))
        buttonLayout.addWidget(self.moveDownButton)

        buttonLayout.addStretch()

        self.tableView.selectionModel().currentChanged.connect(self.onCurrentChanged)
        self.tableView.setFocus(Qt.NoFocusReason)
        self.updateWidgets()


    def addRow(self):
        """ Adds an empty row in the plugin table
        """
        model = self.tableView.model()
        # curIdx = self.tableView.getSectionCurrentIndex()
        curIdx = self.tableView.currentIndex()
        curRow, curCol = curIdx.row(), curIdx.column()
        curRow = model.rowCount() if curRow < 0 else curRow # append at the end if non selected
        curCol = 0 if curCol < 0 else curCol
        model.insertItem(model.createItem(), row=curRow)

        self.tableView.setCurrentCell(curRow, curCol)


    def removeRow(self):
        """ Removes the currently selected row
        """
        model = self.tableView.model()
        # curIdx = self.tableView.getSectionCurrentIndex()
        curIdx = self.tableView.currentIndex()
        curRow = curIdx.row()
        if curRow < 0:
            logger.warning("No row selected so no row removed.")
            return

        model.popItemAtRow(curRow)
        self.tableView.setCurrentCell(min(curRow, model.rowCount() - 1), curIdx.column())


    def moveRow(self, number):
        """ Moves the currently selected row a with a number of positions
        """
        #curIdx = self.tableView.getSectionCurrentIndex()
        model = self.tableView.model()
        curIdx = self.tableView.currentIndex()
        curRow = curIdx.row()
        if curRow < 0:
            logger.warning("No row selected so no row moved.")
            return

        model.moveItem(curRow, curRow + number)
        newRow = max(0, min(curRow + number, model.rowCount() - 1) ) # clip
        self.tableView.setCurrentCell(newRow, curIdx.column())


    def onCurrentChanged(self, _curIdx, _prefIdx):
        """ Called when the current table index changes
        """
        self.updateWidgets()


    def updateWidgets(self):
        """ Enables/disables widgets according to the selected row
        """
        row = self.tableView.currentIndex().row()
        numRows = self.tableView.model().rowCount()

        self.addButton.setEnabled(True)
        self.removeButton.setEnabled(0 <= row < numRows)
        self.moveUpButton.setEnabled(1 <= row < numRows)
        self.moveDownButton.setEnabled(0 <= row < numRows-1)



def main():
    """ Test classes
    """
    import sys
    from pprint import pprint

    from PyQt5 import QtWidgets

    from argos import info
    from argos.utils.logs import make_log_format
    from argos.qt.misc import handleException
    from argos.reg.tabmodel import BaseTableModel, BaseItemStore, BaseItem

    info.DEBUGGING = True
    sys.excepthook = handleException

    logging.basicConfig(level="DEBUG", format=make_log_format())


    app = QtWidgets.QApplication([])

    store = BaseItemStore()


    model = BaseTableModel(store)

    window = TableEditWidget(tableModel=model)
    window.show()

    exitCode = app.exec_()

    print("edited store")
    pprint(store.marshall())





if __name__ == "__main__":
    main()

