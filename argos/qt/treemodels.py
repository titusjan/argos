
import logging

from argos.qt.treeitems import BaseTreeItem
from argos.info import DEBUGGING
from argos.qt import Qt, QtCore, QtSignal, QtSlot
from argos.utils.cls import check_is_a_string, check_class
from argos.widgets.constants import TREE_CELL_SIZE_HINT

logger = logging.getLogger(__name__)


INVISIBLE_ROOT_NAME = '<invisible-root>'

class BaseTreeModel(QtCore.QAbstractItemModel):
    """ Tree model from the editabletreemodel.py example.

        We place an item at the root of the tree of items. This root item corresponds to the null
        model index, QModelIndex(), that is used to represent the parent of a top-level item when
        handling model indexes. Although the root item does not have a visible representation in
        any of the standard views, we use its internal list of QVariant objects to store a list of
        strings that will be passed to views for use as horizontal header titles.

        This BaseTreeModel has one column and can be instantiated for testing purposes.
    """
    HEADERS = tuple('<first column') # override in descendants
    COL_DECORATION = None   # Column number that contains the decoration. None for no icons

    # Can be connected to a QTreeView.update() as to update a single cell
    #update = QtSignal(QtCore.QModelIndex) # Not used

    # Signal emitted when an item has been changed (e.g. by setData). This can be used to update
    # other widgets, whereas the dataChanged signal is used to update the treeView only. This
    # separation is introduced to break circular updates that would occur when the other widgets
    # update the tree model.
    # Inspired by the QStandardItemModel itemChanged signal but named sigItemChanged so that users
    # will see this is argos specific and thus find this definition more easily.
    sigItemChanged = QtSignal(BaseTreeItem)

    def __init__(self, parent=None):
        """ Constructor
        """
        super(BaseTreeModel, self).__init__(parent)

        # The root item is invisible in the tree but is the parent of all items.
        # This way you can have a tree with multiple items at the top level.
        # The root item also is returned by getItem in case of an invalid index.
        # Finally, it is used to store the header data.
        #self._horizontalHeaders = [header for header in headers]
        self._invisibleRootItem = BaseTreeItem(nodeName=INVISIBLE_ROOT_NAME)

        self.cellSizeHint = TREE_CELL_SIZE_HINT # Default cell size, can be overridden by items


    @property
    def invisibleRootItem(self):
        """ Returns the invisible root item, which contains no actual data
        """
        return self._invisibleRootItem


    @property
    def horizontalHeaders(self):
        """ Returns list of horizontal header labels.
            See also self.headerData()
        """
        return self.HEADERS


    ###########################################################
    # These methods re-implement the QAbstractModel interface #
    ###########################################################

    def columnCount(self, _parentIndex=QtCore.QModelIndex()):
        """ Returns the number of columns for the children of the given parent.
            In most subclasses, the number of columns is independent of the parent.
        """
        return len(self.horizontalHeaders)


    @QtSlot(QtCore.QModelIndex, Qt.ItemDataRole)
    def data(self, index, role=Qt.DisplayRole):
        """ Returns the data stored under the given role for the item referred to by the index.

            Calls self.itemData for valid items. Descendants should typically override itemData
            instead of this function.
        """
        try:
            if index.isValid():
                item = self.getItem(index, altItem=self.invisibleRootItem)
                return self.itemData(item, index.column(), role=role)
            else:
                return None
        except Exception as ex:
            # This Qt slot is called directly from the event loop so uncaught exception make the
            # application crash (exceptions can come from plugins here). Instead of crashing we
            # show the error message in the table/tree and hope the users report the error.
            if not DEBUGGING and role in (Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole,
                                          Qt.StatusTipRole, Qt.WhatsThisRole):
                return repr(ex)
            else:
                raise # Still fail hard for the other roles.


    def itemData(self, item, column, role=Qt.DisplayRole):
        """ Returns the data stored under the given role for the item. O
            The column parameter may be used to differentiate behavior per column.

            The default implementation does nothing. Descendants should typically override this
            function instead of data()

            Note: If you do not have a value to return, return an invalid QVariant instead of
            returning 0. (This means returning None in Python)
        """
        if role == Qt.DecorationRole:
            if column == self.COL_DECORATION:
                return item.decoration

        elif role == Qt.FontRole:
            return item.font

        elif role == Qt.ForegroundRole:
            return item.foregroundBrush

        elif role == Qt.BackgroundRole:
            return item.backgroundBrush

        elif role == Qt.SizeHintRole:
            return self.cellSizeHint if item.sizeHint is None else item.sizeHint

        return None


    def flags(self, index):
        """ Returns the item flags for the given index.

            The base class implementation returns a combination of flags that enables the item
            (ItemIsEnabled) and allows it to be selected (ItemIsSelectable).
        """
        if not index.isValid():
            return 0
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """ Returns the data for the given role and section in the header with the specified
            orientation.

            For horizontal headers, the section number corresponds to the column number. Similarly,
            for vertical headers, the section number corresponds to the row number.
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.horizontalHeaders[section]

        return None


    def index(self, row, column, parentIndex=QtCore.QModelIndex()):
        """ Returns the index of the item in the model specified by the given row, column and parent
            index.

            Since each item contains information for an entire row of data, we create a model index
            to uniquely identify it by calling createIndex() it with the row and column numbers and
            a pointer to the item. (In the data() function, we will use the item pointer and column
            number to access the data associated with the model index; in this model, the row number
            is not needed to identify data.)

            When reimplementing this function in a subclass, call createIndex() to generate
            model indexes that other components can use to refer to items in your model.
        """
#        logger.debug("  called index({}, {}, {}) {}"
#                     .format(parentIndex.row(), parentIndex.column(), parentIndex.isValid(),
#                             parentIndex.isValid() and parentIndex.column() != 0))

        parentItem = self.getItem(parentIndex, altItem=self.invisibleRootItem)
        #logger.debug("    Getting row {} from parentItem: {}".format(row, parentItem))

        if not (0 <= row < parentItem.nChildren()):
            # Can happen when deleting the last child.
            #logger.warn("Index row {} invalid for parent item: {}".format(row, parentItem))
            return QtCore.QModelIndex()

        if not (0 <= column < self.columnCount()):
            #logger.warn("Index column {} invalid for parent item: {}".format(column, parentItem))
            return QtCore.QModelIndex()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            logger.warn("No child item found at row {} for parent item: {}".format(row, parentItem))
            return QtCore.QModelIndex()


    def parent(self, index):
        """ Returns the parent of the model item with the given index. If the item has no parent,
            an invalid QModelIndex is returned.

            A common convention used in models that expose tree data structures is that only items
            in the first column have children. For that case, when reimplementing this function in
            a subclass the column of the returned QModelIndex would be 0. (This is done here.)

            When reimplementing this function in a subclass, be careful to avoid calling QModelIndex
            member functions, such as QModelIndex.parent(), since indexes belonging to your model
            will simply call your implementation, leading to infinite recursion.
        """
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = self.getItem(index, altItem=self.invisibleRootItem)
        parentItem = childItem.parentItem

        if parentItem == self.invisibleRootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.childNumber(), 0, parentItem)


    def rowCount(self, parentIndex=QtCore.QModelIndex()):
        """ Returns the number of rows under the given parent. When the parent is valid it means
            that rowCount is returning the number of children of parent.

            Note: When implementing a table based model, rowCount() should return 0 when the parent
            is valid.
        """
        parentItem = self.getItem(parentIndex, altItem=self.invisibleRootItem)
        return parentItem.nChildren()


    def hasChildren(self, parentIndex=QtCore.QModelIndex()):
        """ Returns true if parent has any children; otherwise returns false.
            Use rowCount() on the parent to find out the number of children.
        """
        parentItem = self.getItem(parentIndex, altItem=self.invisibleRootItem)
        return parentItem.hasChildren()


    def setData(self, index, value, role=Qt.EditRole):
        """ Sets the role data for the item at index to value.
            Returns true if successful; otherwise returns false.

            The dataChanged and sigItemChanged signals will be emitted if the data was successfully
            set.

            Descendants should typically override setItemData function instead of setData()
        """
        if role != Qt.CheckStateRole and role != Qt.EditRole:
            return False

        treeItem = self.getItem(index, altItem=self.invisibleRootItem)
        try:
            result = self.setItemData(treeItem, index.column(), value, role=role)
            if result:
                # Emit dataChanged to update the tree view
                # TODO, update the entire tree?
                # A check box can have a tristate checkbox as parent which state depends
                # on the state of this child check box. Therefore we update the parentIndex
                # and the descendants.
                self.emitDataChanged(treeItem)

                # Emit sigItemChanged to update other widgets.
                self.sigItemChanged.emit(treeItem)
            return result

        except Exception as ex:
            # When does this still happen? Can we remove it?
            logger.warn("Unable to set data: {}".format(ex))
            if DEBUGGING:
                raise
            return False



    def setItemData(self, item, column, value, role=Qt.EditRole):
        """ Sets the role data for the item at index to value.

            Descendants should typically override this function instead of setData()
            Should True if successful; otherwise returns false.
        """
        raise NotImplementedError("Please override in descendant class.")



    ##################################################################
    # The methods below are not part of the QAbstractModel interface #
    ##################################################################


    def rootIndex(self):
        """ Returns an invalid index, which therefore will point to the root Item"""
        return QtCore.QModelIndex()


    def rootItem(self):
        """ Returns an invalid index, which therefore will point to the root Item.
            Can return None if the model is empty
        """
        return self.getItem(self.rootIndex())


    # Originally from the editabletreemodel example but added the altItem parameter to force
    # callers to specify request the invisibleRootItem as alternative in case of an invalid index.
    # TODO: rename to ItemFromIndex to be consistent with QStandardItemModel?
    def getItem(self, index, altItem=None):
        """ Returns the TreeItem for the given index. Returns the altItem if the index is invalid.
        """
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        #return altItem if altItem is not None else self.invisibleRootItem # TODO: remove
        return altItem


    def insertItem(self, childItem, position=None, parentIndex=None):
        """ Inserts a childItem before row 'position' under the parent index.

            If position is None the child will be appended as the last child of the parent.
            Returns the index of the new inserted child.
        """
        if parentIndex is None:
            parentIndex=QtCore.QModelIndex()

        parentItem = self.getItem(parentIndex, altItem=self.invisibleRootItem)

        nChildren = parentItem.nChildren()
        if position is None:
            position = nChildren

        assert 0 <= position <= nChildren, \
            "position should be 0 < {} <= {}".format(position, nChildren)

        self.beginInsertRows(parentIndex, position, position)
        try:
            parentItem.insertChild(childItem, position)
        finally:
            self.endInsertRows()

        childIndex = self.index(position, 0, parentIndex)
        assert childIndex.isValid(), "Sanity check failed: childIndex not valid"
        return childIndex


    def removeAllChildrenAtIndex(self, parentIndex):
        """ Removes all children of the item at the parentIndex.
            The children's finalize method is called before removing them to give them a
            chance to close their resources
        """
        if not parentIndex.isValid():
            logger.debug("No valid item selected for deletion (ignored).")
            return

        parentItem = self.getItem(parentIndex, None)
        logger.debug("Removing children of {!r}".format(parentItem))
        assert parentItem, "parentItem not found"

        #firstChildRow = self.index(0, 0, parentIndex).row()
        #lastChildRow = self.index(parentItem.nChildren()-1, 0, parentIndex).row()
        #logger.debug("Removing rows: {} to {}".format(firstChildRow, lastChildRow))
        #self.beginRemoveRows(parentIndex, firstChildRow, lastChildRow)

        self.beginRemoveRows(parentIndex, 0, parentItem.nChildren()-1)
        try:
            parentItem.removeAllChildren()
        finally:
            self.endRemoveRows()

        logger.debug("removeAllChildrenAtIndex completed")


    def deleteItemAtIndex(self, itemIndex):
        """ Removes the item at the itemIndex.
            The item's finalize method is called before removing so it can close its resources.
        """
        if not itemIndex.isValid():
            logger.debug("No valid item selected for deletion (ignored).")
            return

        item = self.getItem(itemIndex, "<no item>")
        logger.debug("deleteItemAtIndex: removing {}".format(item))

        parentIndex = itemIndex.parent()
        parentItem = self.getItem(parentIndex, altItem=self.invisibleRootItem)
        row = itemIndex.row()
        self.beginRemoveRows(parentIndex, row, row)
        try:
            parentItem.removeChild(row)
        finally:
            self.endRemoveRows()

        logger.debug("deleteItemAtIndex completed")


    def replaceItemAtIndex(self, newItem, oldItemIndex):
        """ Removes the item at the itemIndex and insert a new item instead.
        """
        oldItem = self.getItem(oldItemIndex)
        childNumber = oldItem.childNumber()
        parentIndex = oldItemIndex.parent()
        self.deleteItemAtIndex(oldItemIndex)
        insertedIndex = self.insertItem(newItem, position=childNumber, parentIndex=parentIndex)
        return insertedIndex

    # Seems not to be used anymore...
    # def setInvisibleRootItem(self, baseTreeItem=None):
    #     """ Will set the invisible root tree item and reset the model.
    #         All nodes will collapse because of the model reset.
    #
    #         If baseTreeItem is None, a single BaseTreeItem will be added. This effectively
    #         makes the model empty.
    #     """
    #     if baseTreeItem is None:
    #         baseTreeItem = BaseTreeItem(nodeName=INVISIBLE_ROOT_NAME)
    #     check_class(baseTreeItem, BaseTreeItem)
    #
    #     self.beginResetModel()
    #     self._invisibleRootItem = baseTreeItem
    #     self._invisibleRootItem.model = self
    #     self.endResetModel()


    def isTopLevelIndex(self, itemIndex):
        """ Returns true if the index is a direct child of the invisible root item
            Will raise an exception when itemIndex _is_ the invisible root.
        """
        return not itemIndex.parent().isValid()


    def findTopLevelItemIndex(self, childIndex):
        """ Traverses the tree upwards from childItem until its top level ancestor item is found.
            Top level items are items that are direct children of the (invisible) root item.
            This function therefore raises an exception when called with the root item.
        """
        if self.isTopLevelIndex(childIndex):
            return childIndex
        else:
            return self.findTopLevelItemIndex(childIndex.parent())


    def findItemAndIndexPath(self, path, startIndex=None):
        """ Searches all the model recursively (starting at startIndex) for an item where
            item.nodePath == path.

            Returns list of (item, itemIndex) tuples from the start index to that node.
            Raises IndexError if the item cannot be found.

            If startIndex is None, or path starts with a slash, searching begins at the (invisible)
            root item.
        """
        def _getIndexAndItemByName(nodeName, parentItem, parentIndex):
            """ Searches the parent for a direct child having the nodeName.
                Returns (item, itemIndex) tuple. Raises IndexError if the item cannot be found.
            """
            if self.canFetchMore(parentIndex):
                self.fetchMore(parentIndex)

            for rowNr, childItem in enumerate(parentItem.childItems):
                if childItem.nodeName == nodeName:
                    childIndex = self.index(rowNr, 0, parentIndex=parentIndex)
                    return (childItem, childIndex)
            raise IndexError("Item not found: {!r}".format(path))


        def _auxGetByPath(parts, item, index):
            "Aux function that does the actual recursive search"
            #logger.debug("_auxGetByPath item={}, parts={}".format(item, parts))

            if len(parts) == 0:
                return [(item, index)]

            head, tail = parts[0], parts[1:]
            if head == '':
                # Two consecutive slashes. Just go one level deeper.
                return _auxGetByPath(tail, item, index)
            else:
                childItem, childIndex = _getIndexAndItemByName(head, item, index)
                return [(item, index)] + _auxGetByPath(tail, childItem, childIndex)

        # The actual body of findItemAndIndexPath starts here

        check_is_a_string(path)
        if not path:
            raise IndexError("Item not found: {!r}".format(path))

        if startIndex is None or path.startswith('/'):
            startIndex = QtCore.QModelIndex()
            startItem = self.invisibleRootItem
        else:
            startItem = self.getItem(startIndex, None)

        if not startItem:
            raise IndexError("Item not found: {!r}. No start item!".format(path))

        return _auxGetByPath(path.split('/'), startItem, startIndex)


    def __not_used__emitUpdateForBranch(self, parentIndex):
        """ Emits the update signal for parentIndex and all its children.
        """
        self.update.emit(parentIndex)
        for rowNr in range(self.rowCount(parentIndex)):
            childIndex = self.index(rowNr, parentIndex.column(), parentIndex=parentIndex)
            self.emitUpdateForBranch(childIndex)


    def logItems(self, level=logging.DEBUG):
        """ rootItem
        """
        rootItem = self.rootItem()
        if rootItem is None:
            logger.debug("No items in: {}".format(self))
        else:
            rootItem.logBranch(level=level)
