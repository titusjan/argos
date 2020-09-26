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

""" Common functionality, look and feel for all table views in Argos.

    Control-C copies all data.
"""
from __future__ import print_function

import logging
from argos.qt import QtWidgets, Qt


logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901

class ArgosTableView(QtWidgets.QTableView):
    """ QTableView that defines common functionality for argos
    """
    def __init__(self, *args, **kwargs):
        """ Constructor
        """
        super(ArgosTableView, self).__init__(*args, **kwargs)


    def keyPressEvent(self, event):
        """ Overrides key press events to capture Ctrl-C
        """
        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            self.copySelectionToClipboard()
        else:
            super(ArgosTableView, self).keyPressEvent(event)
        return


    def copySelectionToClipboard(self):
        """ Copies selected cells to clipboard.

            Only works for ContiguousSelection
        """
        if not self.model():
            logger.warning("Table contains no data. Copy to clipboard aborted.")
            return

        if self.selectionMode() not in [QtWidgets.QTableView.SingleSelection,
                                        QtWidgets.QTableView.ContiguousSelection]:
            logger.warning("Copy to clipboard does not work for current selection mode: {}"
                           .format(self.selectionMode()))
            return

        selectedIndices = self.selectionModel().selectedIndexes()
        logger.info("Copying {} selected cells to clipboard.".format(len(selectedIndices)))

        # selectedIndexes() can return unsorted list so we sort it here to be sure.
        selectedIndices.sort(key=lambda idx: (idx.row(), idx.column()))

        # Unflatten indices into a list of list of indicides
        allIndices = []
        allLines = []
        lineIndices = []  # indices of current line
        prevRow = None
        for selIdx in selectedIndices:
            if prevRow != selIdx.row() and prevRow is not None: # new line
                allIndices.append(lineIndices)
                lineIndices = []
            lineIndices.append(selIdx)
            prevRow = selIdx.row()
        allIndices.append(lineIndices)
        del lineIndices

        # Convert to tab-separated lines so it can be pasted in Excel.
        lines = []
        for lineIndices in allIndices:
            line = '\t'.join([str(idx.data()) for idx in lineIndices])
            lines.append(line)
        txt = '\n'.join(lines)
        #print(txt)
        QtWidgets.QApplication.clipboard().setText(txt)


