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

""" RTI properties inspector.
"""
import logging

from argos.qt import QtWidgets, QtCore
from argos.repo.detailpanes import DetailTablePane
from argos.repo.repotreemodel import RepoTreeModel

logger = logging.getLogger(__name__)



class PropertiesPane(DetailTablePane):
    """ Shows the properties of the selected repo tree item.

        The properties correspond to a column in the repository tree view but typically those
        columns are hidden to save screen space. That's why this details pane is useful.
    """
    _label = "Properties"

    HEADERS = ["Name", "Value"]
    (COL_PROP_NAME, COL_VALUE) = range(len(HEADERS))

    def __init__(self, repoTreeView, parent=None):
        super(PropertiesPane, self).__init__(repoTreeView, parent=parent)
        self.table.addHeaderContextMenu(enabled = {'Name': False, 'Value': False}) # disable action

        self.table.setTextElideMode(QtCore.Qt.ElideMiddle)

        tableHeader = self.table.horizontalHeader()
        tableHeader.resizeSection(self.COL_PROP_NAME, 125)
        tableHeader.resizeSection(self.COL_VALUE, 150)


    def _drawContents(self, currentRti=None):
        """ Draws the attributes of the currentRTI
        """
        table = self.table
        table.setUpdatesEnabled(False)
        try:
            table.clearContents()
            verticalHeader = table.verticalHeader()
            verticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

            if currentRti is None:
                return

            # Each column in the repo tree corresponds to a row in this detail pane.
            repoModel = self._repoTreeView.model()
            propNames = RepoTreeModel.HEADERS
            table.setRowCount(len(propNames))

            for row, propName in enumerate(propNames):
                nameItem = QtWidgets.QTableWidgetItem(propName)
                nameItem.setToolTip(propName)
                table.setItem(row, self.COL_PROP_NAME, nameItem)
                propValue = repoModel.itemData(currentRti, row)
                propItem = QtWidgets.QTableWidgetItem(propValue)
                propItem.setToolTip(propValue)
                table.setItem(row, self.COL_VALUE, propItem)
                table.resizeRowToContents(row)

            verticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        finally:
            table.setUpdatesEnabled(True)



