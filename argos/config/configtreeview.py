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

""" Configuration tree. Can be used to manipulate the a ConfigurationModel.

"""
from __future__ import print_function

import enum
import logging
import os.path

from argos.config.abstractcti import ResetMode
from argos.config.configitemdelegate import ConfigItemDelegate
from argos.config.configtreemodel import ConfigTreeModel
from argos.info import DEBUGGING, icons_directory
from argos.qt import Qt, QtCore, QtGui, QtWidgets, QtSlot
from argos.widgets.argostreeview import ArgosTreeView
from argos.widgets.constants import RIGHT_DOCK_WIDTH, DOCK_SPACING, DOCK_MARGIN
from argos.widgets.misc import BasePanel
from argos.utils.cls import check_class

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901



class ConfigWidget(BasePanel):
    """ Shows the configuration. At the moment only the confg tree view.
    """

    def __init__(self, configTreeModel, parent=None):
        """ Constructor.
            :param parent:
        """
        super(ConfigWidget, self).__init__(parent=parent)

        # Actions that change the reset mode of the reset button
        self.modeActionGroup = QtWidgets.QActionGroup(self)
        self.modeActionGroup.setExclusive(True)

        self.modeAllAction = QtWidgets.QAction("Reset All", self.modeActionGroup)
        self.modeAllAction.setToolTip("Changes button reset mode to reset all settings")
        self.modeAllAction.setCheckable(True)
        self.modeAllAction.triggered.connect(lambda : self.setResetMode(ResetMode.All))


        self.modeRangeAction = QtWidgets.QAction("Reset Ranges", self.modeActionGroup)
        self.modeRangeAction.setToolTip("Changes button reset mode to reset axes")
        self.modeRangeAction.setCheckable(True)
        self.modeRangeAction.triggered.connect(lambda : self.setResetMode(ResetMode.Ranges))

        # Sanity check that actions have been added to action group
        assert self.modeActionGroup.actions(), "Sanity check. resetActionGroup is empty"

        # Actions that actually reset the settings

        self.resetAllAction = QtWidgets.QAction("Reset All", self)
        self.resetAllAction.setToolTip("Resets all settings.")
        self.resetAllAction.setIcon(QtGui.QIcon(os.path.join(icons_directory(), 'reset-l.svg')))
        self.resetAllAction.setShortcut("Ctrl+=")

        self.resetRangesAction = QtWidgets.QAction("Reset Ranges", self)
        self.resetRangesAction.setToolTip(
            "Resets range of all plots, color scales, table column/row sizes etc.")
        self.resetRangesAction.setIcon(QtGui.QIcon(os.path.join(icons_directory(), 'reset-l.svg')))
        self.resetRangesAction.setShortcut("Ctrl+0")

        self.resetButtonMenu = QtWidgets.QMenu()
        self.resetButtonMenu.addAction(self.resetAllAction)
        self.resetButtonMenu.addAction(self.resetRangesAction)
        self.resetButtonMenu.addSection("Default")
        self.resetButtonMenu.addAction(self.modeAllAction)
        self.resetButtonMenu.addAction(self.modeRangeAction)

        # Widgets

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setSpacing(5)
        self.mainLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)

        self.configTreeView = ConfigTreeView(configTreeModel, parent=self)
        self.mainLayout.addWidget(self.configTreeView)

        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addLayout(self.buttonLayout)

        self.autoCheckBox = QtWidgets.QCheckBox("Auto")
        self.autoCheckBox.setToolTip("Auto reset when a new item or axis is selected.")
        self.autoCheckBox.setChecked(True)

        self.resetButton = QtWidgets.QToolButton()
        self.resetButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.resetButton.setDefaultAction(self.resetButtonMenu.defaultAction())
        self.resetButton.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
        self.resetButton.setMenu(self.resetButtonMenu)

        # Set font size to the same as used for push buttons
        dummyButton = QtWidgets.QPushButton("dummy")
        fontSize = dummyButton.font().pointSize()
        del dummyButton

        logger.debug("Setting QToolButtons font size to: {} point".format(fontSize))
        font = self.resetButton.font()
        font.setPointSizeF(fontSize)
        self.resetButton.setFont(font)

        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.autoCheckBox)
        self.buttonLayout.addWidget(self.resetButton)
        self.buttonLayout.addStretch()

        self.autoCheckBox.stateChanged.connect(self.setAutoReset)
        self.resetRangesAction.triggered.connect(self.configTreeView.resetAllRanges)
        self.resetAllAction.triggered.connect(self.configTreeView.resetAllSettings)

        self.setResetMode(self.configTreeView.resetMode)


    def setAutoReset(self, value):
        """ Sets config tree widget auto reset
        """
        self.configTreeView.autoReset = value


    def setResetMode(self, resetMode):
        """ Sets the reset mode of the reset button reset

            :param resetMode: 'Ranges' all 'All'
        """
        check_class(resetMode, ResetMode)
        if resetMode == ResetMode.All:
            self.resetButton.setDefaultAction(self.resetAllAction)
            self.modeAllAction.setChecked(True)
        elif resetMode == ResetMode.Ranges:
            self.resetButton.setDefaultAction(self.resetRangesAction)
            self.modeRangeAction.setChecked(True)
        else:
            raise ValueError("Unexpected resetMode: {}".format(resetMode))

        self.configTreeView.resetMode = resetMode


    def marshall(self):
        """ Returns a dictionary to save in the persistent settings
        """
        cfg = dict(
            autoRange = self.autoCheckBox.isChecked(),
            resetMode = self.configTreeView.resetMode.value,
        )
        return cfg


    def unmarshall(self, cfg):
        """ Initializes itself from a config dict form the persistent settings.
        """
        if 'autoRange' in cfg:
            self.autoCheckBox.setChecked(cfg['autoRange'])

        if 'resetMode' in cfg:
            self.setResetMode(ResetMode(cfg['resetMode']))



class ConfigTreeView(ArgosTreeView):
    """ Tree widget for manipulating a tree of configuration options.
    """
    def __init__(self, configTreeModel, parent=None):
        """ Constructor
        """
        super(ConfigTreeView, self).__init__(treeModel=configTreeModel, parent=parent)

        self._configTreeModel = configTreeModel

        self.expanded.connect(configTreeModel.expand)
        self.collapsed.connect(configTreeModel.collapse)
        #configTreeModel.update.connect(self.update) # not necessary
        #self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)

        treeHeader = self.header()
        treeHeader.resizeSection(ConfigTreeModel.COL_NODE_NAME, round(RIGHT_DOCK_WIDTH * 0.5))
        treeHeader.resizeSection(ConfigTreeModel.COL_VALUE, round(RIGHT_DOCK_WIDTH * 0.5))

        headerNames = self.model().horizontalHeaders
        enabled = dict((name, True) for name in headerNames)
        enabled[headerNames[ConfigTreeModel.COL_NODE_NAME]] = False # Name cannot be unchecked
        enabled[headerNames[ConfigTreeModel.COL_VALUE]] = False # Value cannot be unchecked
        checked = dict((name, False) for name in headerNames)
        checked[headerNames[ConfigTreeModel.COL_NODE_NAME]] = True # Checked by default
        checked[headerNames[ConfigTreeModel.COL_VALUE]] = True # Checked by default
        self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})

        self.setRootIsDecorated(True)
        self.setUniformRowHeights(True)
        self.setItemDelegate(ConfigItemDelegate())
        self.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)

        #self.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked |
        #                     QtWidgets.QAbstractItemView.EditKeyPressed |
        #                     QtWidgets.QAbstractItemView.AnyKeyPressed |
        #                     QtWidgets.QAbstractItemView.SelectedClicked)


    def sizeHint(self):
        """ The recommended size for the widget."""
        return QtCore.QSize(RIGHT_DOCK_WIDTH, 500)


    @QtSlot(QtWidgets.QWidget, QtWidgets.QAbstractItemDelegate.EndEditHint)
    def closeEditor(self, editor, hint):
        """ Finalizes, closes and releases the given editor.
        """
        # It would be nicer if this method was part of ConfigItemDelegate since createEditor also
        # lives there. However, QAbstractItemView.closeEditor is sometimes called directly,
        # without the QAbstractItemDelegate.closeEditor signal begin emitted, e.g when the
        # currentItem changes. Therefore we cannot connect the QAbstractItemDelegate.closeEditor
        # signal to a slot in the ConfigItemDelegate.
        configItemDelegate = self.itemDelegate()
        configItemDelegate.finalizeEditor(editor)

        super(ConfigTreeView, self).closeEditor(editor, hint)


    def expandBranch(self, index=None, expanded=None):
        """ Expands or collapses the node at the index and all it's descendants.
            If expanded is True the nodes will be expanded, if False they will be collapsed, and if
            expanded is None the expanded attribute of each item is used.
            If parentIndex is None, the invisible root will be used (i.e. the complete forest will
            be expanded).
        """
        configModel = self.model()
        if index is None:
            #index = configTreeModel.createIndex()
            index = QtCore.QModelIndex()

        if index.isValid():
            if expanded is None:
                item = configModel.getItem(index)
                self.setExpanded(index, item.expanded)
            else:
                self.setExpanded(index, expanded)

        for rowNr in range(configModel.rowCount(index)):
            childIndex = configModel.index(rowNr, configModel.COL_NODE_NAME, parentIndex=index)
            self.expandBranch(index=childIndex, expanded=expanded)


    @property
    def autoReset(self):
        """ Indicates that the model will be (oartially) reset when the RTI or combo change
        """
        return self._configTreeModel.autoReset


    @autoReset.setter
    def autoReset(self, value):
        """ Indicates that the model will be (oartially) reset when the RTI or combo change
        """
        self._configTreeModel.autoReset = value


    @property
    def resetMode(self):
        """ Determines what is reset if autoReset is True (either axes or all settings)
        """
        return self._configTreeModel.resetMode


    @resetMode.setter
    def resetMode(self, value):
        """ Determines what is reset if autoReset is True (either axes or all settings)
        """
        self._configTreeModel.resetMode = value


    def resetAllSettings(self):
        """ Resets all settings
        """
        logger.debug("Resetting all settings")
        self._configTreeModel.resetAllSettings()


    def resetAllRanges(self):
        """ Resets all (axis/color/etc) range settings.
        """
        logger.debug("Resetting all range settings")
        self._configTreeModel.resetAllRanges()
