#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2010 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################

import logging
from libargos.qt import QtCore

logger = logging.getLogger(__name__)
    
# Placed TreeItem in the same module as BaseTreeModel since they are meant to be used together.

class BaseTreeItem(object):
    """ Base class for storing item data in a tree form. Each tree item represents a row
        in the BaseTreeModel (QAbstractItemModel). 
        
        The tree items have no notion of which field is stored in which column. This is implemented
        in BaseTreeModel._itemValueForColumn
    """
    def __init__(self):
        self._parentItem = None
        self._childItems = [] # the fetched children

    def finalize(self):
        """ Can be used to cleanup resources. Should be called explicitly.
            Finalizes its children before closing itself
        """
        for child in self.childItems:
            child.finalize()
        
    def __repr__(self):
        return "<{}>".format(type(self).__name__)
    
    @property
    def parentItem(self):
        """ The parent item """
        return self._parentItem
    
    @parentItem.setter
    def parentItem(self, value):
        """ The parent item """
        self._parentItem = value
    
    @property
    def childItems(self):
        """ List of child items """
        #logger.debug("childItems {!r}".format(self))
        return self._childItems

    def hasChildren(self):
        """ Returns True if the item has children 
        """
        return len(self.childItems) > 0

    def child(self, row):
        return self.childItems[row]

    def nChildren(self):
        return len(self.childItems)

    def childNumber(self):
        """ Gets the index (nr) of this node in its parent's list of children
        """
        if self.parentItem != None:
            return self.parentItem.childItems.index(self)
        return 0


    def insertChild(self, childItem, position=None): 
        
        if position is None:
            position = self.nChildren()
            
        assert 0 <= position <= len(self.childItems), \
            "position should be 0 < {} <= {}".format(position, len(self.childItems))
            
        assert childItem.parentItem is None, "childItem already has a parent: {}".format(childItem)
            
        childItem.parentItem = self    
        self.childItems.insert(position, childItem)


    def removeChild(self, position):
        """ Removes the child at the position 'position'
            Calls the child item finalize to close its resources before removing it.
        """
        assert 0 <= position <= len(self.childItems), \
            "position should be 0 < {} <= {}".format(position, len(self.childItems))

        self.childItems[position].finalize()
        self.childItems.pop(position)


    def removeAllChildren(self):
        """ Removes the all children of this node.
            Calls the child items finalize to close their resources before removing them.
        """
        for childItem in self.childItems:
            childItem.finalize()
        self._childItems = []


    
class AbstractLazyLoadTreeItem(BaseTreeItem):
    """ Abstract base class for a tree item that can do lazy loading of children.
        Descendants should override the _fetchAllChildren
    """
    def __init__(self):
        """ Constructor
        """
        super(AbstractLazyLoadTreeItem, self).__init__()
        self._childrenFetched = False
        
    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children 
        """
        return True
        #return not self._childrenFetched or len(self.childItems) > 0 TODO: use this? 
        
    def canFetchChildren(self):
        return not self._childrenFetched
        
    def fetchChildren(self):
        assert not self._childrenFetched, "canFetchChildren must be True"
        childItems = self._fetchAllChildren()
        self._childrenFetched = True
        return childItems
    
    def _fetchAllChildren(self):
        """ The function that actually fetches the children.
        
            The result must be a list of RepoTreeItems. Their parents must be None, 
            as that attribute will be set by BaseTreeitem.insertItem()
         
            :rtype: list of BaseRti objects
        """ 
        raise NotImplementedError
    
    def removeAllChildren(self):
        """ Removes all children """
        super(AbstractLazyLoadTreeItem, self).removeAllChildren()
        self._childrenFetched = False
        

    
class BaseTreeModel(QtCore.QAbstractItemModel):
    """ Tree model from the editabletreemodel.py example.
    
        We place an item at the root of the tree of items. This root item corresponds to the null 
        model index, QModelIndex(), that is used to represent the parent of a top-level item when 
        handling model indexes. Although the root item does not have a visible representation in 
        any of the standard views, we use its internal list of QVariant objects to store a list of 
        strings that will be passed to views for use as horizontal header titles.
    """
    HEADERS = tuple() # override in descendants
    COL_ICON = 0      # Column number that contains the icon
    
    def __init__(self, parent=None):
        """ Constructor
        """
        super(BaseTreeModel, self).__init__(parent)

        # The root item is invisible in the tree but is the parent of all items.
        # This way you can have a tree with multiple items at the top level.
        # The root item also is returned by getItem in case of an invalid index. 
        # Finally, it is used to store the header data.
        #self._horizontalHeaders = [header for header in headers]
        self._rootItem = BaseTreeItem()
        
        # To easy turn-on off editing flags without having to override the flags() member
        self._isEditable = True 


    @property
    def rootItem(self):
        """ Returns the invisible root item, which contains no actual data
        """
        return self._rootItem
    

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


    def _itemValueForColumn(self, treeItem, column):
        """ Descendants should override this function to return the value of the item 
            for the given column number.
        """
        raise NotImplementedError("Abstract class.")
    
        
    def data(self, index, role):
        """ Returns the data stored under the given role for the item referred to by the index.
        
            Note: If you do not have a value to return, return an invalid QVariant instead of 
            returning 0. (This means returning None in Python)
        """
        if not index.isValid():
            return None

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            item = self.getItem(index, altItem=self.rootItem)
            return self._itemValueForColumn(item, index.column())
        
        elif role == QtCore.Qt.DecorationRole:
            if index.column() == self.COL_ICON:
                item = self.getItem(index, altItem=self.rootItem)
                return item.icon
        
        return None


    def flags(self, index):
        """ Returns the item flags for the given index.
        
            The base class implementation returns a combination of flags that enables the item 
            (ItemIsEnabled) and allows it to be selected (ItemIsSelectable).
        """
        if not index.isValid():
            return 0
        
        if self._isEditable:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """ Returns the data for the given role and section in the header with the specified 
            orientation.
            
            For horizontal headers, the section number corresponds to the column number. Similarly, 
            for vertical headers, the section number corresponds to the row number.
        """
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
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
        
        parentItem = self.getItem(parentIndex, altItem=self.rootItem)
        #logger.debug("    Getting row {} from parentItem: {}".format(row, parentItem))
        
        if not (0 <= row < parentItem.nChildren()):
            # Can happen when deleting the last child. TODO: remove warning.
            logger.warn("Index row {} invalid for parent item: {}".format(row, parentItem))
            return QtCore.QModelIndex()
        
        if not (0 <= column < self.columnCount()):
            logger.warn("Index column {} invalid for parent item: {}".format(row, parentItem))
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

        childItem = self.getItem(index, altItem=self.rootItem)
        parentItem = childItem.parentItem

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.childNumber(), 0, parentItem)
    

    def rowCount(self, parentIndex=QtCore.QModelIndex()):
        """ Returns the number of rows under the given parent. When the parent is valid it means 
            that rowCount is returning the number of children of parent.

            Note: When implementing a table based model, rowCount() should return 0 when the parent 
            is valid.
        """
        parentItem = self.getItem(parentIndex, altItem=self.rootItem)
        return parentItem.nChildren()


    def hasChildren(self, parentIndex=QtCore.QModelIndex()):
        """ Returns true if parent has any children; otherwise returns false.
            Use rowCount() on the parent to find out the number of children.
        """
        parentItem = self.getItem(parentIndex, altItem=self.rootItem)
        return parentItem.hasChildren()
        


    def _setItemValueForColumn(self, treeItem, column, value):
        """ Descendants should override this function to set the value corresponding
            to the column number in treeItem.
            It should return True for success, otherwise False.
        """
        raise NotImplementedError("Abstract class.")    


    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """ Sets the role data for the item at index to value.
            Returns true if successful; otherwise returns false.
            
            The dataChanged() signal should be emitted if the data was successfully set.
        """
        if role != QtCore.Qt.EditRole:
            return False

        treeItem = self.getItem(index, altItem=self.rootItem)
        result = self._setItemValueForColumn(treeItem, index.column(), value)
        if result:
            self.dataChanged.emit(index, index)
        return result
    

    ##################################################################
    # The methods below are not part of the QAbstractModel interface #
    ##################################################################
    
    
    # Originally from the editabletreemodel example but added the altItem parameter to force
    # callers to specify request the rootItem as alternative in case of an invalid index.
    def getItem(self, index, altItem=None):
        """ Returns the TreeItem for the given index. Returns the altItem if the index is invalid.
        """
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
            
        #return altItem if altItem is not None else self.rootItem # TODO: remove
        return altItem
        

    def insertItem(self, childItem, position=None, parentIndex=QtCore.QModelIndex()):
        """ Inserts a childItem before row 'position' under the parent index.
        
            If position is None the child will be appended as the last child of the parent.
            Returns the index of the new inserted child.
        """
        parentItem = self.getItem(parentIndex, altItem=self.rootItem)
        
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
            The the children's finalize method is closed before removing them to give a
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
            
    
    def deleteItemByIndex(self, itemIndex): 
        """ Removes the item at the itemIndex.
            The item's finalize method is called before removing so it can close its resources. 
        """
        if not itemIndex.isValid():
            logger.debug("No valid item selected for deletion (ignored).")
            return
        
        item = self.getItem(itemIndex, "<no item>")
        logger.debug("deleteItemByIndex: removing {!r}".format(item))
        
        parentIndex = itemIndex.parent()
        parentItem = self.getItem(parentIndex, altItem=self.rootItem)
        row = itemIndex.row()
        self.beginRemoveRows(parentIndex, row, row)
        try:
            parentItem.removeChild(row)
        finally:
            self.endRemoveRows()
            
        logger.debug("deleteItemByIndex completed")
  

    def replaceItemAtIndex(self, newItem, oldItemIndex): 
        """ Removes the item at the itemIndex and insert a new item instead.
        """
        oldItem = self.getItem(oldItemIndex)
        childNumber = oldItem.childNumber()
        parentIndex = oldItemIndex.parent()
        self.deleteItemByIndex(oldItemIndex)
        insertedIndex = self.insertItem(newItem, position=childNumber, parentIndex=parentIndex)
        return insertedIndex


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
            

