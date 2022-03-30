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
import os.path
import sys

from argos.info import icons_directory
from argos.qt import QtCore, QtGui, QtWidgets, Qt, QtSlot
from argos.qt.colorselect import ColorSelectWidget
from argos.qt.shortcutedit import ShortCutEditor
from argos.reg.basereg import BaseRegistryModel, BaseRegistry, RegType
from argos.reg.tabview import TableEditWidget
from argos.utils.cls import check_class
from argos.utils.misc import wrapHtmlColor
from argos.widgets.constants import MONO_FONT, FONT_SIZE, COLOR_ERROR
#from argos.widgets.constants import QCOLOR_REGULAR, QCOLOR_NOT_IMPORTED, QCOLOR_ERROR

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
        check_class(registry, BaseRegistry)

        self._label = label
        self._orgRegistry = registry
        self._registry = copy.deepcopy(registry)  # make copy so changes can be canceled
        self._tableModel = self._registry.createTableModel(parent=self)
        self.mapper = QtWidgets.QDataWidgetMapper(parent=self)
        self.mapper.setModel(self._tableModel)

        self.setWindowTitle("Argos {} Plugins".format(label))

        layout = QtWidgets.QVBoxLayout(self)

        self.verSplitter = QtWidgets.QSplitter(Qt.Vertical)
        #self.verSplitter.setCollapsible(1, False)
        self.verSplitter.setChildrenCollapsible(False)
        layout.addWidget(self.verSplitter)

        self.tableWidget = TableEditWidget(self._tableModel)
        self.verSplitter.addWidget(self.tableWidget)

        self._tableView = self.tableWidget.tableView
        self._tableView.installEventFilter(self)

        # Form
        self.horSplitter = QtWidgets.QSplitter(Qt.Horizontal)
        self.horSplitter.setChildrenCollapsible(False)

        self.verSplitter.addWidget(self.horSplitter)

        self.formWidget = QtWidgets.QWidget()
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formWidget.setLayout(self.formLayout)
        self.horSplitter.addWidget(self.formWidget)

        self._editWidgets = []
        itemCls = registry.ITEM_CLASS
        assert len(itemCls.LABELS) == len(itemCls.TYPES), \
            "Regtype Mismatch: {} != {}".format(len(itemCls.LABELS), len(itemCls.TYPES))
        for col, (label, regType) in enumerate(zip(itemCls.LABELS, itemCls.TYPES)):

            if regType == RegType.String:
                editWidget = QtWidgets.QLineEdit()
                self.mapper.addMapping(editWidget, col)
            elif regType == RegType.ShortCut:
                editWidget = ShortCutEditor()
                self.mapper.addMapping(editWidget, col)
            elif regType == RegType.ColorStr:
                editWidget = ColorSelectWidget()
                self.mapper.addMapping(editWidget.lineEditor, col)
            else:
                raise AssertionError("Unexpected regType: {}".format(regType))
            editWidget.installEventFilter(self)
            self.formLayout.addRow(label, editWidget)
            self._editWidgets.append(editWidget)

        # Detail info widget
        font = QtGui.QFont()
        font.setFamily(MONO_FONT)
        font.setFixedPitch(True)
        font.setPointSize(FONT_SIZE)

        self.editor = QtWidgets.QTextEdit()
        self.editor.setReadOnly(True)
        #self.editor.setFocusPolicy(Qt.NoFocus) # Allow focus so that user can copy text from it.
        #self.editor.setFont(font)
        self.editor.setWordWrapMode(QtGui.QTextOption.WordWrap)
        self.editor.clear()
        self.horSplitter.addWidget(self.editor)

        self.horSplitter.setStretchFactor(0, 2)
        self.horSplitter.setStretchFactor(1, 3)
        self.verSplitter.setSizes([300, 150])

        # Reset/Cancel/Save Buttons

        self.saveButton = QtWidgets.QPushButton("Save")
        self.saveButton.clicked.connect(self.accept)

        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)

        self.resetButton = QtWidgets.QPushButton("Reset Table to Defaults...")
        self.resetButton.clicked.connect(self.resetToDefaults)
        self.resetButton.setIcon(QtGui.QIcon(os.path.join(icons_directory(), 'reset-l.svg')))

        # We use a button layout instead of a QButtonBox because there always will be a default
        # button (e.g. the Save button) that will light up, even if another widget has the focus.
        # From https://doc.qt.io/archives/qt-4.8/qdialogbuttonbox.html#details
        #   However, if there is no default button set and to preserve which button is the default
        #   button across platforms when using the QPushButton::autoDefault property, the first
        #   push button with the accept role is made the default button when the QDialogButtonBox
        #   is shown,

        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout.addWidget(self.resetButton)
        self.buttonLayout.addStretch()
        if sys.platform == 'darwin':
            self.buttonLayout.addWidget(self.cancelButton)
            self.buttonLayout.addWidget(self.saveButton)
        else:
            self.buttonLayout.addWidget(self.saveButton)
            self.buttonLayout.addWidget(self.cancelButton)
        layout.addLayout(self.buttonLayout)

        # Connect signals and populate

        self.tableWidget.tableView.selectionModel().currentChanged.connect(self.currentItemChanged)
        self.tableWidget.tableView.model().sigItemChanged.connect(self._updateEditor)

        self.resize(QtCore.QSize(1100, 700))
        self.tableWidget.tableView.setFocus(Qt.NoFocusReason)

        self.tryImportAllPlugins()



    def eventFilter(self, targetWidget, event):
        """ Toggles the focus between table and edit form when the return key is pressed.
        """
        if event.type() == QtCore.QEvent.KeyPress and event.key() in (Qt.Key_Enter, Qt.Key_Return):

            if (event.modifiers() & Qt.ControlModifier):
                self.accept()
                return True

            if targetWidget in self._editWidgets:
                self._tableView.setFocus()
                return True

            elif targetWidget == self._tableView:
                curIdx = self._tableView.currentIndex()
                col = curIdx.column() if curIdx.isValid() else 0
                self._editWidgets[col].setFocus()
                return True

        # Give parent event filter chance to filter the event. Otherwise targetWidget will get it.
        return super(PluginsDialog, self).eventFilter(targetWidget, event)


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
        super(PluginsDialog, self).accept()


    def resetToDefaults(self):
        """ Resets the registry to it's default values
        """
        button = QtWidgets.QMessageBox.question(
            self, "Reset {}".format(self._label), "Reset plugins to the default set?")

        if button != QtWidgets.QMessageBox.Yes:
            logger.info("Resetting registry canceled.")
            return None

        logger.info("Resetting {} registry to its default.".format(self._label))
        self._tableModel.beginResetModel()
        try:
            self._registry.unmarshall(cfg={}) #  Empty config will cause the defaults to be used.
            self.tryImportAllPlugins()
        finally:
            self._tableModel.endResetModel()


    def tryImportAllPlugins(self):
        """ Tries to import all underlying plugin classes
        """
        logger.debug("Importing all plugins.")

        for regItem in self._registry.items:
            if not regItem.triedImport:
                self._tableModel.tryImportRegItem(regItem)

        logger.debug("Importing finished.")


    def getCurrentRegItem(self):
        """ Returns the item that is currently selected in the table.
            Can return None if there is no data in the table
        """
        return self.tableWidget.tableView.getCurrentItem()


    @QtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def currentItemChanged(self, currentIndex=None, _previousIndex=None):
        """ Updates the description text widget when the user clicks on a selector in the table.
            The _currentIndex and _previousIndex parameters are ignored.
        """
        self.mapper.setCurrentModelIndex(currentIndex)
        regItem = self.getCurrentRegItem()
        self._updateEditor(regItem)


    def _updateEditor(self, regItem):
        """ Updates the editor with contents of the currently selected regItem
        """
        self.editor.clear()

        if regItem is None:
            return

        header = "<h2>{}</h2>".format(regItem.name)

        if regItem.successfullyImported is None:
            html = header + 'Plugin not yet imported!'
            self.editor.setHtml(wrapHtmlColor(html, COLOR_ERROR))
        elif regItem.successfullyImported is False:
            html = "{}Unable to import plugin.\n\nError: {}".format(header, regItem.exception)
            if hasattr(regItem.exception, "traceBackString"):
                html += "<pre>{}</pre>".format(regItem.exception.traceBackString)
            self.editor.setHtml(wrapHtmlColor(html, COLOR_ERROR))
        elif regItem.descriptionHtml:
            self.editor.setHtml(header.replace('\n', '<br>') + regItem.descriptionHtml)
        else:
            self.editor.setHtml(header + regItem.docString.replace('\n', '<br>'))

