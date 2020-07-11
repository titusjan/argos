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

""" Dialog window that allows users to configure the installed plugins.
"""
from __future__ import print_function

import copy
import logging

from argos.qt import QtCore, QtGui, QtWidgets, Qt, QtSlot
from argos.reg.basereg import BaseRegistryModel
from argos.reg.tabview import TableEditWidget
from argos.utils.cls import check_class
from argos.widgets.constants import MONO_FONT, FONT_SIZE
from argos.widgets.constants import QCOLOR_REGULAR, QCOLOR_NOT_IMPORTED, QCOLOR_ERROR

logger = logging.getLogger(__name__)

# The main window inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201



class PluginsDialog(QtWidgets.QDialog):
    """ Dialog window that allows users to configure the installed plugins.
    """

    def __init__(self, label, registry,  parent=None):
        """ Constructor
        """
        super(PluginsDialog, self).__init__(parent=parent)

        self.label = label
        self._orgRegistry = registry
        self._registry = copy.deepcopy(registry)  # make copy so changes can be canceled
        self.setWindowTitle("Argos Plugins")

        layout = QtWidgets.QVBoxLayout(self)

        splitter = QtWidgets.QSplitter(Qt.Vertical)
        layout.addWidget(splitter)

        self.tableModel = BaseRegistryModel(self._registry)
        self.tableWidget = TableEditWidget(self.tableModel)
        splitter.addWidget(self.tableWidget)

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

        # Buttons
        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

        self.tableWidget.tableView.selectionModel().currentChanged.connect(self.currentItemChanged)
        self.tableWidget.tableView.model().sigItemChanged.connect(self._updateEditor)

        self.resize(QtCore.QSize(1100, 700))
        self.tableWidget.tableView.setFocus(Qt.NoFocusReason)

        self.tryImportAllPlugins()


    def accept(self):
        """ Saves registry.

            After saving the application may be in an inconsistent state. For instance, files
            may be opened with plugins that no longer exist. Therefore the caller must 'restart'
            the application if the changes were accepted.
        """
        logger.debug("Updating registry from dialog")

        # Copy contents from copy back to the original registry
        self._orgRegistry.clear()
        self._orgRegistry.unmarshall(self._registry.marshall())
        super().accept()



    def tryImportAllPlugins(self):
        """ Tries to import all underlying plugin classes
        """
        logger.debug("Importing all plugins.")

        model = self.tableWidget.tableView.model()
        for regItem in self._registry.items:
            if not regItem.triedImport:
                model.tryImportRegItem(regItem)

        logger.debug("Importing finished.")


    def getCurrentRegItem(self):
        """ Returns the item that is currently selected in the table.
            Can return None if there is no data in the table
        """
        return self.tableWidget.tableView.getCurrentItem()


    @QtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def currentItemChanged(self, _currentIndex=None, _previousIndex=None):
        """ Updates the description text widget when the user clicks on a selector in the table.
            The _currentIndex and _previousIndex parameters are ignored.
        """
        regItem = self.getCurrentRegItem()
        self._updateEditor(regItem)


    def _updateEditor(self, regItem):
        """ Updates the editor with contents of the currently selected regItem
        """
        self.editor.clear()
        self.editor.setTextColor(QCOLOR_REGULAR)

        if regItem is None:
            return

        header = "{}\n{}\n\n".format(regItem.name, len(regItem.name) * '=')

        if regItem.successfullyImported is None:
            self.editor.setTextColor(QCOLOR_NOT_IMPORTED)
            self.editor.setPlainText(header + '<plugin not yet imported>')
        elif regItem.successfullyImported is False:
            self.editor.setTextColor(QCOLOR_ERROR)
            self.editor.setPlainText("{}Unable to import plugin.\n\nError: {}"
                                     .format(header, regItem.exception))
        elif regItem.descriptionHtml:
            self.editor.setHtml(header.replace('\n', '<br>') + regItem.descriptionHtml)
        else:
            self.editor.setPlainText(header + regItem.docString)


