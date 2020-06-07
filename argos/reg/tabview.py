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

from argos.utils.cls import type_name, check_class

from argos.reg.tabmodel import BaseTableModel
from argos.qt import QtCore, QtGui, QtWidgets, Qt
from argos.qt.togglecolumn import ToggleColumnTableView


logger = logging.getLogger(__name__)


class BaseTableView(ToggleColumnTableView):
    """ Editable QTableView that shows the contents of a BaseTableModel.
    """
    def __init__(self, model=None, onlyShowImported=False, parent=None):
        """ Constructor

            :param model: a RegistryTableModel that maps the regItems
            :param parent: the parent widget
        """
        super(BaseTableView, self).__init__(parent)

        if model is not None:
            check_class(model, BaseTableModel)
            self.setModel(model)
        else:
            assert False, "not yet implemented"

        #self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        #self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        verHeader = self.verticalHeader()
        verHeader.setSectionsMovable(True)

        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        #self.setSortingEnabled(True)
        self.setTabKeyNavigation(False)

        #self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        #self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        Qiv = QtWidgets.QAbstractItemView
        self.setEditTriggers(Qiv.DoubleClicked | Qiv.SelectedClicked | Qiv.EditKeyPressed)
        #self.setWordWrap(True)

        tableHeader = self.horizontalHeader()
        tableHeader.setDefaultAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        tableHeader.setSectionResizeMode(QtWidgets.QHeaderView.Interactive) # don't set to stretch
        tableHeader.setStretchLastSection(True)


    def getCurrentRegItem(self):
        """ Find the regItem that is currently selected.
        """
        return self.model().itemFromIndex(self.currentIndex())


    def setCurrentRegItem(self, regItem):
        """ Sets the current registry item.
        """
        rowIndex = self.model().indexFromItem(regItem)
        if not rowIndex.isValid():
            logger.warning("Can't select {!r} in table".format(regItem))
        self.setCurrentIndex(rowIndex)




class TableEditWidget(QtWidgets.QWidget):
    """ Widget that contains a table plus buttons to update it

    """
    def __init__(self, tableModel=None, parent=None):
        """ Constructor.
        """
        super(TableEditWidget, self).__init__(parent=parent)

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)

        self.tableView = BaseTableView(tableModel)
        self.mainLayout.addWidget(self.tableView)

        buttonLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addLayout(buttonLayout)

        self.addButton = QtWidgets.QPushButton("Add")
        self.addButton.clicked.connect(self.addRow)
        buttonLayout.addWidget(self.addButton)

        self.removeButton = QtWidgets.QPushButton("Remove")
        self.removeButton.clicked.connect(self.removeRow)
        buttonLayout.addWidget(self.removeButton)
        buttonLayout.addStretch()

        self.tableView.setFocus(Qt.NoFocusReason)


    def addRow(self):
        """ Adds an empty row in the plugin table
        """
        curIdx = self.tableView.currentIndex()
        curRow = curIdx.row()
        if curRow < 0:
            curRow = None

        model = self.tableView.model()
        model.insertItem(model.createItem(), row=curRow)


    def removeRow(self):
        """ Adds remove the currently selected row
        """
        curIdx = self.tableView.currentIndex()
        curRow = curIdx.row()
        if curRow < 0:
            logger.warning("No row selected so no row removed.")
            return

        self.tableView.model().removeItemAtRow(curRow)



def main():
    """ Test classes
    """
    import sys
    from pprint import pprint

    from PyQt5 import QtWidgets

    from argos import info
    from argos.utils.misc import make_log_format
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

    exitCode = app.exec()

    print("edited store")
    pprint(store.marshall())





if __name__ == "__main__":
    main()

