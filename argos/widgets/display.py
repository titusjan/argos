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

""" Widgets for displaying messages
"""
from __future__ import print_function

import logging

from argos.qt import Qt, QtGui, QtWidgets
from argos.widgets.constants import MONO_FONT, FONT_SIZE

logger = logging.getLogger(__name__)


# The main window inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201


class MessageDisplay(QtWidgets.QWidget):
    """ Widget that shows a label and title.
        Consists of a title label and a larger message label for details.
    """
    def __init__(self, parent=None, msg="", title="Error"):
        super(MessageDisplay, self).__init__(parent)

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.titleLabel = QtWidgets.QLabel(title)
        self.titleLabel.setTextFormat(Qt.PlainText)
        self.titleLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.titleLabel.setAlignment(Qt.AlignHCenter)
        self.layout.addWidget(self.titleLabel, stretch=0)

        font = QtGui.QFont()
        font.setFamily(MONO_FONT)
        font.setFixedPitch(True)
        font.setPointSize(FONT_SIZE)

        self.messageLabel = QtWidgets.QLabel(msg)
        self.messageLabel.setFont(font)
        self.messageLabel.setTextFormat(Qt.PlainText)
        self.messageLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.messageLabel.setWordWrap(True)
        self.messageLabel.setAlignment(Qt.AlignTop)
        self.messageLabel.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Plain)
        self.layout.addWidget(self.messageLabel, stretch=1)


    def setError(self, msg=None, title=None):
        """ Shows and error message
        """
        if msg is not None:
            self.messageLabel.setText(msg)

        if title is not None:
            self.titleLabel.setText(title)


