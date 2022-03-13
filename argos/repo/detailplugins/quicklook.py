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

""" RTI quicklook.
"""
import logging

import numpy as np

from argos.qt import QtGui, QtWidgets
from argos.repo.detailpanes import DetailBasePane
from argos.widgets.constants import MONO_FONT, FONT_SIZE

logger = logging.getLogger(__name__)


class QuickLookPane(DetailBasePane):
    """ Shows a string representation of the RTI contents.
    """
    _label = "Quick Look"

    def __init__(self, repoTreeView, parent=None):
        super(QuickLookPane, self).__init__(repoTreeView, parent=parent)

        self._currentRti = None

        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.editor.setFont(QtGui.QFont(MONO_FONT, FONT_SIZE))

        self.contentsLayout.addWidget(self.editor)


    def _drawContents(self, currentRti=None):
        """ Draws the attributes of the currentRTI
        """
        self._currentRti = currentRti

        if self._currentRti is None:
            self.editor.clear()
        else:
            editorCharWidth =  self.editor.width() / self.editor.fontMetrics().averageCharWidth()
            oldLineWidth = np.get_printoptions()['linewidth']
            np.set_printoptions(linewidth=editorCharWidth)
            try:
                self.editor.setPlainText(self._currentRti.quickLook(editorCharWidth))
            finally:
                np.set_printoptions(linewidth=oldLineWidth)


    def resizeEvent(self, event):
        """ Called when the panel is resized. Will update the line length of the editor.
        """
        self.repoItemChanged(self._currentRti) # call repoItemChanged so it handles exceptions
        super(QuickLookPane, self).resizeEvent(event)

