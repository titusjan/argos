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

from argos.qt import QtWidgets, QtSlot, Qt

from argos.inspector.registry import InspectorRegItem
from argos.widgets.constants import DOCK_MARGIN, DOCK_SPACING
from argos.widgets.misc import setWidgetSizePolicy

logger = logging.getLogger(__name__)

NO_INSPECTOR_LABEL = '<No Inspector>'


class InspectorSelectionPane(QtWidgets.QFrame):
    """ Shows the attributes of the selected repo tree item
    """

    def __init__(self, inspectorActionGroup, parent=None):
        super(InspectorSelectionPane, self).__init__(parent=parent)

        # self.setFrameShape(QtWidgets.QFrame.Box)
        self.menuButton = QtWidgets.QPushButton(NO_INSPECTOR_LABEL)
        self.menuButton.setMinimumWidth(10)

        inspectorMenu = QtWidgets.QMenu("Change Inspector", parent=self.menuButton)
        for action in inspectorActionGroup.actions():
            inspectorMenu.addAction(action)
        self.menuButton.setMenu(inspectorMenu)

        self.messageLabel = QtWidgets.QLabel("")
        self.messageLabel.setObjectName("message_label")
        self.messageLabel.setFrameStyle(QtWidgets.QFrame.Panel)
        self.messageLabel.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.messageLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)
        self.setLayout(self.mainLayout)

        self.mainLayout.addWidget(self.menuButton, stretch=0)
        self.mainLayout.addWidget(self.messageLabel, stretch=1)

        setWidgetSizePolicy(self.menuButton, hor=QtWidgets.QSizePolicy.Minimum)
        setWidgetSizePolicy(self.messageLabel, hor=QtWidgets.QSizePolicy.Ignored)
        setWidgetSizePolicy(
            self, hor=QtWidgets.QSizePolicy.MinimumExpanding, ver=QtWidgets.QSizePolicy.Fixed)


    def showMessage(self, msg):
        """ Sets the message label to a message text
        """
        logger.debug("Show message to user: '{}'".format(msg))
        self.messageLabel.setText(msg)
        self.messageLabel.setToolTip(msg)


    @QtSlot(InspectorRegItem)
    def updateFromInspectorRegItem(self, inspectorRegItem):
        """ Updates the label from the full name of the InspectorRegItem
        """
        label = NO_INSPECTOR_LABEL if inspectorRegItem is None else inspectorRegItem.name
        self.menuButton.setText(label)
