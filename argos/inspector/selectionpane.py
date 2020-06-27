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
from argos.widgets.constants import DOCK_MARGIN, DOCK_SPACING

logger = logging.getLogger(__name__)

NO_INSPECTOR_LABEL = '<No Inspector>'


class InspectorSelectionPane(QtWidgets.QFrame):
    """ Shows the attributes of the selected repo tree item
    """

    def __init__(self, inspectorActionGroup, parent=None):
        super(InspectorSelectionPane, self).__init__(parent=parent)

        #self.setFrameShape(QtWidgets.QFrame.Box)
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setSpacing(DOCK_SPACING)
        self.mainLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)
        self.setLayout(self.mainLayout)

        # self.label = QtWidgets.QLabel("Current inspector")
        # self.layout.addWidget(self.label)

        self.menuButton = QtWidgets.QPushButton(NO_INSPECTOR_LABEL)
        self.menuButton.setMinimumWidth(10)
        self.mainLayout.addWidget(self.menuButton)

        inspectorMenu = QtWidgets.QMenu("Change Inspector", parent=self.menuButton)
        for action in inspectorActionGroup.actions():
            inspectorMenu.addAction(action)
        self.menuButton.setMenu(inspectorMenu)

        sizePolicy = self.sizePolicy()
        sizePolicy.setVerticalPolicy(QtWidgets.QSizePolicy.Fixed)
        self.setSizePolicy(sizePolicy)


    @QtSlot(InspectorRegItem)
    def updateFromInspectorRegItem(self, inspectorRegItem):
        """ Updates the label from the full name of the InspectorRegItem
        """
        label = NO_INSPECTOR_LABEL if inspectorRegItem is None else inspectorRegItem.name
        self.menuButton.setText(label)
