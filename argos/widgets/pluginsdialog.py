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

"""
    PluginsDialog window that shows which plugins are registered.
"""
from __future__ import print_function

import logging

from argos.qt.registry import ClassRegItem
from argos.qt.registrytable import RegistryTableModel, RegistryTableProxyModel, RegistryTableView
from argos.qt.registrytable import QCOLOR_REGULAR, QCOLOR_NOT_IMPORTED, QCOLOR_ERROR
from argos.qt import QtCore, QtGui, QtWidgets, Qt, QtSlot
from argos.utils.cls import check_class
from argos.widgets.constants import MONO_FONT, FONT_SIZE

logger = logging.getLogger(__name__)

# The main window inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201


class RegistryTab(QtWidgets.QWidget):
    """ Tab that shows the contents of a single plugin registry.

    """
    def __init__(self, registry, parent=None,
                 attrNames=None, headerNames=None, headerSizes=None,
                 onlyShowImported=False, importOnSelect=True):
        """ Constructor.

            If onlyShowImported is True, regItems that are not (successfully) imported are
            filtered from the table. By default onlyShowImported is False.

            If importOnSelect is True (the default), the item is imported if the user
            selects it.
        """
        super(RegistryTab, self).__init__(parent=parent)
        self._importOnSelect = importOnSelect
        self._onlyShowImported = onlyShowImported
        self._registry = registry


        attrNames = [] if attrNames is None else attrNames
        headerNames = attrNames if headerNames is None else headerNames
        headerSizes = [] if headerSizes is None else headerSizes
        if headerSizes is None:
            headerSizes = []
        else:
            assert len(headerSizes) == len(attrNames), \
                "Size mismatch {} != {}".format(len(headerSizes), len(attrNames))

        layout = QtWidgets.QVBoxLayout(self)
        statusLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(statusLayout)

        self.statusLabel = QtWidgets.QLabel("")
        statusLayout.addWidget(self.statusLabel)
        statusLayout.setStretch(0, 1)

        self.loadAllButton = QtWidgets.QPushButton("Load all")
        self.loadAllButton.setFocusPolicy(Qt.ClickFocus)
        self.loadAllButton.clicked.connect(self.tryImportAllPlugins)
        statusLayout.addWidget(self.loadAllButton)
        statusLayout.setStretch(1, 0)

        splitter = QtWidgets.QSplitter(Qt.Vertical)
        layout.addWidget(splitter)

        # Table
        tableModel = RegistryTableModel(self._registry, attrNames=attrNames, parent=self)
        proxyTableModel = RegistryTableProxyModel(parent=self,
                                                  onlyShowImported=self._onlyShowImported)
        proxyTableModel.setSourceModel(tableModel)
        self.tableView = RegistryTableView(proxyTableModel, onlyShowImported=self.onlyShowImported)

        tableHeader = self.tableView.horizontalHeader()
        for col, headerSize in enumerate(headerSizes):
            if headerSize:
                tableHeader.resizeSection(col, headerSize)

        selectionModel = self.tableView.selectionModel()
        selectionModel.currentRowChanged.connect(self.currentItemChanged)

        splitter.addWidget(self.tableView)
        splitter.setCollapsible(0, False)

        # Detail info widget
        font = QtGui.QFont()
        font.setFamily(MONO_FONT)
        font.setFixedPitch(True)
        font.setPointSize(FONT_SIZE)

        self.editor = QtWidgets.QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setFont(font)
        self.editor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.editor.clear()
        splitter.addWidget(self.editor)
        splitter.setCollapsible(1, False)
        splitter.setSizes([300, 150])

        self.tableView.setFocus(Qt.NoFocusReason)


    @property
    def onlyShowImported(self):
        "If True, regItems that are not (successfully) imported are filtered from in the table"
        return self._onlyShowImported


    @property
    def registeredItems(self):
        "Returns the items from the registry"
        return self._registry.items


    def importRegItem(self, regItem):
        """ Imports the regItem
            Writes this in the statusLabel while the import is in progress.
        """
        self.statusLabel.setText("Importing {}...".format(regItem.fullName))
        QtWidgets.qApp.processEvents()
        regItem.tryImportClass()
        self.tableView.model().emitDataChanged(regItem)
        self.statusLabel.setText("")
        QtWidgets.qApp.processEvents()


    def tryImportAllPlugins(self):
        """ Tries to import all underlying plugin classes
        """
        for regItem in self.registeredItems:
            if not regItem.triedImport:
                self.importRegItem(regItem)

        logger.debug("Importing finished.")


    def getCurrentRegItem(self):
        """ Returns the item that is currently selected in the table.
            Can return None if there is no data in the table
        """
        return self.tableView.getCurrentRegItem()


    def setCurrentRegItem(self, regItem):
        """ Sets the current item to the regItem
        """
        check_class(regItem, ClassRegItem, allow_none=True)
        self.tableView.setCurrentRegItem(regItem)


    @QtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def currentItemChanged(self, _currentIndex=None, _previousIndex=None):
        """ Updates the description text widget when the user clicks on a selector in the table.
            The _currentIndex and _previousIndex parameters are ignored.
        """
        self.editor.clear()
        self.editor.setTextColor(QCOLOR_REGULAR)

        regItem = self.getCurrentRegItem()

        if regItem is None:
            return

        if self._importOnSelect and regItem.successfullyImported is None:
            self.importRegItem(regItem)

        if regItem.successfullyImported is None:
            self.editor.setTextColor(QCOLOR_NOT_IMPORTED)
            self.editor.setPlainText('<plugin not yet imported>')
        elif regItem.successfullyImported is False:
            self.editor.setTextColor(QCOLOR_ERROR)
            self.editor.setPlainText(str(regItem.exception))
        elif regItem.descriptionHtml:
            self.editor.setHtml(regItem.descriptionHtml)
        else:
            self.editor.setPlainText(regItem.docString)



class PluginsDialog(QtWidgets.QDialog):
    """ Dialog window that shows the installed plugins.
    """

    def __init__(self,
                 inspectorRegistry=None,
                 rtiRegistry=None,
                 parent=None):
        """ Constructor
        """
        super(PluginsDialog, self).__init__(parent=parent)

        self.setWindowTitle("Installed Argos Plugins")
        self.setModal(False)

        layout = QtWidgets.QVBoxLayout(self)

        self.tabWidget = QtWidgets.QTabWidget()
        layout.addWidget(self.tabWidget)

        attrNames = ['fullName', 'fullClassName', 'pythonPath']
        headerSizes = [200, 300, None]

        if inspectorRegistry:
            inspectorTab = RegistryTab(inspectorRegistry,
                                       attrNames=attrNames, headerSizes=headerSizes)
            self.tabWidget.addTab(inspectorTab, "Inspectors")

        if rtiRegistry:
            rtiTab = RegistryTab(rtiRegistry,
                                 attrNames=attrNames, headerSizes=headerSizes)
            self.tabWidget.addTab(rtiTab, "File Formats")

        # Sort by fullName by default.
        for tabNr in range(self.tabWidget.count()):
            self.tabWidget.widget(tabNr).tableView.sortByColumn(0, Qt.AscendingOrder)

        # Buttons
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)
        layout.addWidget(buttonBox)

        self.resize(QtCore.QSize(1100, 700))


    def tryImportAllPlugins(self):
        """ Refreshes the tables of all tables by importing the underlying classes
        """
        logger.debug("Importing plugins: {}".format(self))
        for tabNr in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(tabNr)
            tab.tryImportAllPlugins()


