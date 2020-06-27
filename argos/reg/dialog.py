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
from argos.reg.tabmodel import BaseTableModel
from argos.reg.tabview import TableEditWidget


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

        self.tableModel = BaseTableModel(self._registry)
        self.tableWidget = TableEditWidget(self.tableModel)
        layout.addWidget(self.tableWidget)

        # Buttons
        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

        self.resize(QtCore.QSize(1100, 700))


    def tryImportAllPlugins(self):
        """ Refreshes the tables of all tables by importing the underlying classes
        """
        logger.debug("Importing plugins: {}".format(self))
        for tabNr in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(tabNr)
            tab.tryImportAllPlugins()


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
