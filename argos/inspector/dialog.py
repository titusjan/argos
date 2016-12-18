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
    OpenInspectorDialog dialog window that lets the user pick a new inspector.
"""
from __future__ import print_function

import logging

from argos.qt import Qt, QtCore, QtWidgets
from argos.inspector.registry import InspectorRegItem
from argos.utils.cls import check_class
from argos.widgets.pluginsdialog import RegistryTab


logger = logging.getLogger(__name__)


# The main window inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201

class OpenInspectorDialog(QtWidgets.QDialog):
    """ Dialog window that allows the user to open an inspector plugins.

        SIDE EFFECT: will try to import all underlying inspector classes.
            This is done so that help and number of dimensions can be displayed.
    """

    def __init__(self, registry, onlyShowImported=False, parent=None):
        """ Constructor
        """
        super(OpenInspectorDialog, self).__init__(parent=parent)

        self._registry = registry

        self.setWindowTitle('Open Inspector')
        self.setModal(True)
        layout = QtWidgets.QVBoxLayout(self)

        attrNames = ['name', 'library', 'nDims']
        headerSizes = [250, 250, None]

        self.inspectorTab = RegistryTab(registry, attrNames=attrNames, headerSizes=headerSizes,
                                        onlyShowImported=onlyShowImported)
        self.inspectorTab.tableView.sortByColumn(1, Qt.AscendingOrder) # sort by library
        layout.addWidget(self.inspectorTab)

        # Buttons
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                           QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

        # Double clicking is equivalent to selecting it and clicking Ok.
        self.inspectorTab.tableView.doubleClicked.connect(self.accept)

        self.resize(QtCore.QSize(800, 600))

        #self.inspectorTab.tryImportAllPlugins()


    def getCurrentInspectorRegItem(self):
        """ Returns the inspector that is currently selected in the table.
            Can return None if there is no data in the table
        """
        return self.inspectorTab.getCurrentRegItem()


    def setCurrentInspectorRegItem(self, regItem):
        """ Sets the current inspector given an InspectorRegItem
        """
        check_class(regItem, InspectorRegItem, allow_none=True)
        self.inspectorTab.setCurrentRegItem(regItem)



