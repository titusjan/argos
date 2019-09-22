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

""" Inspector Selection Pane
"""
import logging

from argos.qt import QtWidgets, QtSlot

from argos.inspector.registry import InspectorRegItem
from argos.widgets.misc import BasePanel
from argos.widgets.constants import DOCK_MARGIN, DOCK_SPACING

logger = logging.getLogger(__name__)



def addInspectorActionsToMenu(inspectorMenu, execInspectorDialogAction, inspectorActionGroup):
    """ Adds menu items to the inpsectorMenu for the given set-inspector actions.

        :param inspectorMenu: inspector menu that will be modified
        :param execInspectorDialogAction: the "Browse Inspectors..." actions
        :param inspectorActionGroup: action group with actions for selecting a new inspector
        :return: the inspectorMenu, which has been modified.
    """
    inspectorMenu.addAction(execInspectorDialogAction)
    inspectorMenu.addSeparator()

    for action in inspectorActionGroup.actions():
        inspectorMenu.addAction(action)

    return inspectorMenu


class InspectorSelectionPane(BasePanel):
    """ Shows the attributes of the selected repo tree item
    """
    def __init__(self, execInspectorDialogAction, inspectorActionGroup, parent=None):
        super(InspectorSelectionPane, self).__init__(parent=parent)

        #self.setFrameShape(QtWidgets.QFrame.Box)
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setSpacing(DOCK_SPACING)
        self.mainLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)
        self.setLayout(self.mainLayout)


        # self.label = QtWidgets.QLabel("Current inspector")
        # self.layout.addWidget(self.label)

        self.menuButton = QtWidgets.QPushButton("No inspector")
        self.menuButton.setMinimumWidth(10)
        self.mainLayout.addWidget(self.menuButton)

        inspectorMenu = QtWidgets.QMenu("Change Inspector", parent=self.menuButton)
        addInspectorActionsToMenu(inspectorMenu, execInspectorDialogAction, inspectorActionGroup)
        self.menuButton.setMenu(inspectorMenu)

        sizePolicy = self.sizePolicy()
        sizePolicy.setVerticalPolicy(QtWidgets.QSizePolicy.Fixed)
        self.setSizePolicy(sizePolicy)


    @QtSlot(InspectorRegItem)
    def updateFromInspectorRegItem(self, inspectorRegItem):
        """ Updates the label from the full name of the InspectorRegItem
        """
        library, name = inspectorRegItem.splitName()
        #label = "{} ({})".format(name, library) if library else name
        label = name
        #self.label.setText(label)
        self.menuButton.setText(label)
