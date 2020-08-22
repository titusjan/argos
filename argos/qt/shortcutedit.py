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


class ShortCutEditor(QtWidgets.QLineEdit):

    def __init__(self, parent=None):
        super(ShortCutEditor, self).__init__(parent=parent)


    def keyPressEvent(self, event):

        key = event.key()

        if (Qt.Key_A <= key <= Qt.Key_Z or Qt.Key_0 <= key <= Qt.Key_9 or
            Qt.Key_F1 <= key <= Qt.Key_F35):

            seq = QtGui.QKeySequence(event.modifiers()|event.key()).toString()

            logger.debug("Key press event: {}: {}".format(event.key(), seq))
            self.setText(seq)
        else:
            super(ShortCutEditor, self).keyPressEvent(event)
        return
