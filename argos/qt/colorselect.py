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

""" Color selector functionality. E.g. for use in the plugin config dialog
"""
import logging
from argos.qt import QtCore, QtGui, QtWidgets, Qt
from argos.utils.defs import InvalidInputError

logger = logging.getLogger(__name__)

class ColorSelectWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(ColorSelectWidget, self).__init__(parent=parent)

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.mainLayout)

        self.lineEditor = QtWidgets.QLineEdit()
        self.lineEditor.setToolTip("Color hex code: a '#' followed by 6 hex-digits.")
        self.mainLayout.addWidget(self.lineEditor)
        self.setFocusProxy(self.lineEditor)

        regExp = QtCore.QRegExp(r'#[0-9A-F]{6}', Qt.CaseInsensitive)
        validator = QtGui.QRegExpValidator(regExp, parent=self)
        self.lineEditor.setValidator(validator)

        self.pickButton = QtWidgets.QPushButton()
        self.pickButton.setText("Color Picker...")
        self.pickButton.setToolTip("Open color dialog.")
        self.pickButton.setFocusPolicy(Qt.NoFocus)
        self.pickButton.clicked.connect(self.openColorDialog)

        self.mainLayout.addWidget(self.pickButton)


    def setData(self, qColor):
        """ Provides the main editor widget with a data to manipulate.
        """
        self.lineEditor.setText(qColor.name().upper())
        self.lineEditor.setFocus(Qt.OtherFocusReason)  #


    def getData(self):
        """ Gets data from the editor widget.
        """
        text = self.lineEditor.text()
        if not text.startswith('#'):
            text = '#' + text

        validator = self.lineEditor.validator()
        if validator is not None:
            state, text, _ = validator.validate(text, 0)
            if state != QtGui.QValidator.Acceptable:
                raise InvalidInputError("Invalid input: {!r}".format(text))

        return  text


    def openColorDialog(self):
        """ Opens a QColorDialog for the user
        """
        try:
            currentColor = self.getData()
        except InvalidInputError:
            currentColor = "#FFFFFF"

        qColor = QtWidgets.QColorDialog.getColor(QtGui.QColor(currentColor), self)

        if qColor.isValid():
            self.setData(qColor)
