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

""" RTI dimensions inspector.
"""
import logging

from argos.qt import Qt, QtWidgets, QtCore
from argos.repo.detailpanes import DetailTablePane

logger = logging.getLogger(__name__)



class DimensionsPane(DetailTablePane):
    """ Shows the dimensions of the selected repo tree item.

        Each RTI that is sliceable has a number of dimensions. Each dimension has a size.
        For some types of RTIs (e.g. NcdfVariableRTIs), the dimension represented stored by another, (TODO: implement)
        dedicated RTI. In that case the dimension has a name and path. Otherwise, for example with
        an ArrayRti, the names of the dimensions will be: 'dim0', 'dim1', etc.
    """
    _label = "Dimensions"

    HEADERS = ["Name", "Size", "Group"]
    (COL_NAME, COL_SIZE, COL_GROUP) = range(len(HEADERS))

    def __init__(self, repoTreeView, parent=None):
        super(DimensionsPane, self).__init__(repoTreeView, parent=parent)
        self.table.addHeaderContextMenu(enabled = {'Name': False, 'Size': False}) # disable action

        self.table.setTextElideMode(QtCore.Qt.ElideMiddle)

        tableHeader = self.table.horizontalHeader()
        tableHeader.resizeSection(self.COL_NAME, 125)
        tableHeader.resizeSection(self.COL_SIZE, 125)
        tableHeader.resizeSection(self.COL_GROUP, 250)


    def _drawContents(self, currentRti=None):
        """ Draws the attributes of the currentRTI
        """
        table = self.table
        table.setUpdatesEnabled(False)

        sizeAlignment = Qt.AlignRight | Qt.AlignVCenter

        try:
            table.clearContents()
            verticalHeader = table.verticalHeader()
            verticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

            if currentRti is None or not currentRti.isSliceable:
                return

            nDims = currentRti.nDims
            dimNames = currentRti.dimensionNames
            dimGroups = currentRti.dimensionGroupPaths
            dimSizes = currentRti.arrayShape

            # Sanity check
            assert len(dimNames) == nDims, "dimNames size {} != {}".format(len(dimNames), nDims)
            assert len(dimGroups) == nDims, "dimGroups size {} != {}".format(len(dimGroups), nDims)
            assert len(dimSizes) == nDims, "dimSizes size {} != {}".format(len(dimSizes), nDims)

            table.setRowCount(nDims)
            for row, (dimName, dimSize, dimGroup) in enumerate(zip(dimNames, dimSizes, dimGroups)):
                table.setItem(row, self.COL_NAME, QtWidgets.QTableWidgetItem(dimName))
                table.setItem(row, self.COL_SIZE, QtWidgets.QTableWidgetItem(str(dimSize)))
                table.item(row, self.COL_SIZE).setTextAlignment(sizeAlignment)
                table.setItem(row, self.COL_GROUP, QtWidgets.QTableWidgetItem(str(dimGroup)))
                table.resizeRowToContents(row)

            verticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        finally:
            table.setUpdatesEnabled(True)



