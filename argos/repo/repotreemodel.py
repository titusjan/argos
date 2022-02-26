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

""" Data repository functionality
"""
import logging
from argos.qt import Qt, QtCore
from argos.qt.treemodels import BaseTreeModel
#from argos.info import DEBUGGING
from argos.repo.filesytemrtis import createRtiFromFileName
from argos.repo.baserti import BaseRti
from argos.repo.registry import ICON_COLOR_UNDEF, RtiRegItem
from argos.utils.cls import to_string, type_name, check_class
from argos.utils.dirs import normRealPath

# The cast to int is necessary to avoid a bug in PySide, See:
# https://bugreports.qt-project.org/browse/PYSIDE-20
ALIGN_LEFT  = int(Qt.AlignVCenter | Qt.AlignLeft)
ALIGN_RIGHT = int(Qt.AlignVCenter | Qt.AlignRight)


logger = logging.getLogger(__name__)

class RepoTreeModel(BaseTreeModel):
    """ An implementation QAbstractItemModel that offers read-only access of the application data
        for QTreeViews. The underlying data is stored as repository tree items (BaseRti
        descendants).
    """
    HEADERS = ["Name", "Path", "Dimensions", "Shape", "Kind",
               "Element Type", "Type", "Unit", "Missing data", "Chunking", "Summary",
               "File name", "Item class", "Is open", "Error"]

    (COL_NODE_NAME, COL_NODE_PATH, COL_DIMS, COL_SHAPE, COL_KIND,
     COL_ELEM_TYPE, COL_TYPE, COL_UNIT, COL_MISSING_DATA, COL_CHUNKING, COL_SUMMARY,
     COL_FILE_NAME, COL_RTI_TYPE, COL_IS_OPEN, COL_EXCEPTION) = range(len(HEADERS))

    COL_DECORATION = COL_NODE_NAME  # Column number that contains the icon. None for no icons


    def __init__(self, parent=None):
        """ Constructor
        """
        super(RepoTreeModel, self).__init__(parent=parent)
        self._invisibleRootTreeItem = BaseRti(nodeName='<invisible-root>', iconColor='#FFFFFF')
        self._invisibleRootTreeItem.model = self
        self._isEditable = False


    def itemData(self, treeItem, column, role=Qt.DisplayRole):
        """ Returns the data stored under the given role for the item. O
        """
        if role == Qt.DisplayRole:
            if column == self.COL_NODE_NAME:
                return treeItem.nodeName
            elif column == self.COL_NODE_PATH:
                return treeItem.nodePath
            elif column == self.COL_DIMS:
                if treeItem.isSliceable:
                    return " × ".join(str(elem) for elem in treeItem.dimensionNames)
                else:
                    return ""
            elif column == self.COL_SHAPE:
                if treeItem.isSliceable:
                    return " × ".join(str(elem) for elem in treeItem.arrayShape)
                else:
                    return ""
            elif column == self.COL_IS_OPEN:
                # Only show for RTIs that actually open resources.
                # TODO: this must be clearer. Use CanFetchChildren? Set is Open to None by default?
                if treeItem.hasChildren():
                    return str(treeItem.isOpen)
                else:
                    return ""
            elif column == self.COL_KIND:
                return treeItem.dimensionality
            elif column == self.COL_ELEM_TYPE:
                return treeItem.elementTypeName
            elif column == self.COL_TYPE:
                return treeItem.typeName
            elif column == self.COL_FILE_NAME:
                return treeItem.fileName if hasattr(treeItem, 'fileName') else ''
            elif column == self.COL_UNIT:
                return treeItem.unit
            elif column == self.COL_CHUNKING:
                return treeItem.chunksString
            elif column == self.COL_MISSING_DATA:
                return to_string(treeItem.missingDataValue, noneFormat='') # empty str for Nones
            elif column == self.COL_RTI_TYPE:
                return type_name(treeItem)
            elif column == self.COL_EXCEPTION:
                return str(treeItem.exception) if treeItem.exception else ''
            elif column == self.COL_SUMMARY:
                return treeItem.summary
            else:
                raise ValueError("Invalid column: {}".format(column))

        elif role == Qt.ToolTipRole:
            if treeItem.exception:
                return str(treeItem.exception)
            if column == self.COL_NODE_NAME:
                return treeItem.nodePath # Also path when hovering over the name
            elif column == self.COL_NODE_PATH:
                return treeItem.nodePath
            elif column == self.COL_DIMS:
                if treeItem.isSliceable:
                    if treeItem.dimensionPaths is not None:
                        return " ×\n".join(str(elem) for elem in treeItem.dimensionPaths)
                    else:
                        return " × ".join(str(elem) for elem in treeItem.dimensionNames)
                else:
                    return ""
            elif column == self.COL_SHAPE:
                if treeItem.isSliceable:
                    return " × ".join(str(elem) for elem in treeItem.arrayShape)
                else:
                    return ""
            elif column == self.COL_UNIT:
                return treeItem.unit
            elif column == self.COL_CHUNKING:
                return treeItem.chunksString
            elif column == self.COL_MISSING_DATA:
                return to_string(treeItem.missingDataValue, noneFormat='') # empty str for Nones
            elif column == self.COL_RTI_TYPE:
                return type_name(treeItem)
            elif column == self.COL_KIND:
                return treeItem.dimensionality
            elif column == self.COL_ELEM_TYPE:
                return treeItem.elementTypeName
            elif column == self.COL_TYPE:
                return treeItem.typeName
            elif column == self.COL_FILE_NAME:
                return treeItem.fileName if hasattr(treeItem, 'fileName') else ''
            elif column == self.COL_SUMMARY:
                return treeItem.summary
            else:
                return None

        elif role == Qt.TextAlignmentRole:
            if column == self.COL_SUMMARY:
                return ALIGN_RIGHT
            else:
                return ALIGN_LEFT

        else:
            return super(RepoTreeModel, self).itemData(treeItem, column, role=role)


    def canFetchMore(self, parentIndex):
        """ Returns true if there is more data available for parent; otherwise returns false.
        """
        parentItem = self.getItem(parentIndex)
        if not parentItem:
            return False

        return parentItem.canFetchChildren()


    def fetchMore(self, parentIndex):
        """ Fetches any available data for the items with the parent specified by the parent index.
        """
        parentItem = self.getItem(parentIndex)
        if not parentItem:
            return

        if not parentItem.canFetchChildren():
            return

        for childItem in parentItem.fetchChildren():
            self.insertItem(childItem, parentIndex=parentIndex)

        # Check that Rti implementation correctly sets canFetchChildren
        assert not parentItem.canFetchChildren(), \
            "not all children fetched: {}".format(parentItem)


    def findFileRtiIndex(self, childIndex):
        """ Traverses the tree upwards from the item at childIndex until the tree
            item is found that represents the file the item at childIndex
        """
        parentIndex = childIndex.parent()
        if not parentIndex.isValid():
            return childIndex
        else:
            parentItem = self.getItem(parentIndex)
            childItem = self.getItem(childIndex)
            if parentItem.fileName == childItem.fileName:
                return self.findFileRtiIndex(parentIndex)
            else:
                return childIndex


    def reloadFileAtIndex(self, itemIndex, rtiRegItem=None):
        """ Reloads the item at the index by removing the repo tree item and inserting a new one.

            The new item will have by of type rtiClass. If rtiRegItem is None (the default), the
            new rtiClass will be the same as the old one.
        """
        fileRtiParentIndex = itemIndex.parent()
        fileRti = self.getItem(itemIndex)
        position = fileRti.childNumber()
        fileName = fileRti.fileName

        # Delete old RTI and Insert a new one instead.
        self.deleteItemAtIndex(itemIndex) # this will close the items resources.

        if rtiRegItem is None:
            # Do NOT autodetect but use the class from the the RTI that's being replaced.
            rtiClass = type(fileRti)
            logger.debug("Recreating class from previous RTI class: {}".format(rtiClass))
            repoTreeItem = rtiClass.createFromFileName(fileName, fileRti.iconColor)

            assert repoTreeItem.parentItem is None, "repoTreeItem {!r}".format(repoTreeItem)
            return self.insertItem(repoTreeItem, position=position, parentIndex=fileRtiParentIndex)

        else:
            return self.loadFile(fileName, rtiRegItem, position=position,
                                 parentIndex=fileRtiParentIndex)


    def loadFile(self, fileName, rtiRegItem,
                 position=None, parentIndex=QtCore.QModelIndex()):
        """ Loads a file in the repository as a repo tree item of class rtiClass.
            Autodetects the RTI type if rtiClass is None.
            If position is None the child will be appended as the last child of the parent.
            Returns the index of the newly inserted RTI
        """
        check_class(rtiRegItem, RtiRegItem, allow_none=True)
        fileName = normRealPath(fileName)
        logger.info("Loading data from: {!r}".format(fileName))

        rtiClass = rtiRegItem.getClass(tryImport=True) if rtiRegItem else None
        if rtiClass is None:
            repoTreeItem = createRtiFromFileName(fileName)
        else:
            repoTreeItem = rtiClass.createFromFileName(fileName, rtiRegItem.iconColor)

        assert repoTreeItem.parentItem is None, "repoTreeItem {!r}".format(repoTreeItem)
        return self.insertItem(repoTreeItem, position=position, parentIndex=parentIndex)


