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

from argos.qt import QtGui, QtWidgets
from argos.repo.detailpanes import DetailBasePane

logger = logging.getLogger(__name__)


class QuickLookPane(DetailBasePane):
    """ Shows a string represention of the RTI contents.
    """
    _label = "Quick Look"

    def __init__(self, repoTreeView, parent=None):
        super(QuickLookPane, self).__init__(repoTreeView, parent=parent)

        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setWordWrapMode(QtGui.QTextOption.NoWrap)

        self.contentsLayout.addWidget(self.editor)


    def _drawContents(self, currentRti=None):
        """ Draws the attributes of the currentRTI
        """
        if currentRti is None:
            self.editor.clear()
        else:
            self.editor.setPlainText(currentRti.quickLook)
