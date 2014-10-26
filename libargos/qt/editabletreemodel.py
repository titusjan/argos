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

# Placed TreeItem in the same module as TreeModel since they are meant to be used together.

class TreeItem(object):
    def __init__(self, data, parentItem=None):
        self.parentItem = parentItem
        self.itemData = data
        self.childItems = []
        
    def __repr__(self):
        return "<TreeItem value={}>".format(self.itemData[1])

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def childNumber(self):
        if self.parentItem != None:
            return self.parentItem.childItems.index(self)
        return 0

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        return self.itemData[column]


    def insertChild(self, childItem, position): 
        
        assert 0 <= position <= len(self.childItems), \
            "position should be 0 < {} <= {}".format(position, len(self.childItems))
            
        assert childItem.parentItem is None, "childItem already has a parent"
            
        childItem.parentItem = self    
        self.childItems.insert(position, childItem)


    def removeChild(self, position):
        
        assert 0 <= position <= len(self.childItems), \
            "position should be 0 < {} <= {}".format(position, len(self.childItems))

        self.childItems.pop(position)


    def setData(self, column, value): 
        
        # TODO: remove this check and return value
        if column < 0 or column >= len(self.itemData):
            return False

        self.itemData[column] = value

        return True
    
    
    
class TreeModel(QtCore.QAbstractItemModel):
    """ Tree model from the editabletreemodel.py example.
    
        We place an item at the root of the tree of items. This root item corresponds to the null 
        model index, QModelIndex(), that is used to represent the parent of a top-level item when 
        handling model indexes. Although the root item does not have a visible representation in 
        any of the standard views, we use its internal list of QVariant objects to store a list of 
        strings that will be passed to views for use as horizontal header titles.
    """
    
    def __init__(self, headers, parent=None):
        """ Constructor
        """
        super(TreeModel, self).__init__(parent)

        # The root item is invisible in the tree but is the parent of all items.
        # This way you can have a tree with multiple items at the top level.
        # The root item also is returned by getItem in case of an invalid index. 
        # Finally, it is used to store the header data.
        rootData = [header for header in headers]
        self.rootItem = TreeItem(rootData)


    ###########################################################
    # These methods re-implement the QAbstractModel interface #
    ###########################################################
    
    def columnCount(self, _parentIndex=QtCore.QModelIndex()):
        """ Returns the number of columns for the children of the given parent.
            In most subclasses, the number of columns is independent of the parent.
        """
        return self.rootItem.columnCount()


    def data(self, index, role):
        """ Returns the data stored under the given role for the item referred to by the index.
        
            Note: If you do not have a value to return, return an invalid QVariant instead of 
            returning 0. (This means returning None in Python.)
        """
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return None

        item = self.getItem(index, altItem=self.rootItem)
        return item.data(index.column())


    def flags(self, index):
        """ Returns the item flags for the given index.
        
            The base class implementation returns a combination of flags that enables the item 
            (ItemIsEnabled) and allows it to be selected (ItemIsSelectable).
        """
        if not index.isValid():
            return 0

        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable



    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """ Returns the data for the given role and section in the header with the specified 
            orientation.
            
            For horizontal headers, the section number corresponds to the column number. Similarly, 
            for vertical headers, the section number corresponds to the row number.
        """
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return None


    def index(self, row, column, parentIndex=QtCore.QModelIndex()):
        """ Returns the index of the item in the model specified by the given row, column and parent 
            index. 
            
            In this model, we only return model indexes for child items if the parent index is 
            invalid (corresponding to the root item) or if it has a zero column number.
            
            Since each item contains information for an entire row of data, we create a model index 
            to uniquely identify it by calling createIndex() it with the row and column numbers and 
            a pointer to the item. (In the data() function, we will use the item pointer and column 
            number to access the data associated with the model index; in this model, the row number
            is not needed to identify data.)
            
            When reimplementing this function in a subclass, call createIndex() to generate 
            model indexes that other components can use to refer to items in your model.
        """
        #logger.debug("called index()")
        #logger.debug("  parentIndex.isValid(): {}".format(parentIndex.isValid()))
        #logger.debug("  parentIndex.column(): {}".format(parentIndex.column()))
        if parentIndex.isValid() and parentIndex.column() != 0:
            return QtCore.QModelIndex()

        parentItem = self.getItem(parentIndex, altItem=self.rootItem)
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
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
        return parentItem.childCount()


    def hasChildren(self, parentIndex=QtCore.QModelIndex()):
        """ Returns true if parent has any children; otherwise returns false.

            Use rowCount() on the parent to find out the number of children.
        """
        return self.rowCount(parentIndex) > 0


    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """ Sets the role data for the item at index to value.
            Returns true if successful; otherwise returns false.
            
            The dataChanged() signal should be emitted if the data was successfully set.
        """
        if role != QtCore.Qt.EditRole:
            return False

        item = self.getItem(index, altItem=self.rootItem)
        result = item.setData(index.column(), value)

        if result:
            self.dataChanged.emit(index, index)

        return result
    

    def setHeaderData(self, section, orientation, value, role=QtCore.Qt.EditRole):
        """ Sets the data for the given role and section in the header with the specified 
            orientation to the value supplied.
            
            Returns true if the header's data was updated; otherwise returns false.
            
            When reimplementing this function, the headerDataChanged() signal must be emitted 
            explicitly.
        """
        assert False, "not needed since we don't insert columns."
        if role != QtCore.Qt.EditRole or orientation != QtCore.Qt.Horizontal:
            return False

        result = self.rootItem.setData(section, value)
        if result:
            self.headerDataChanged.emit(orientation, section, section)

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
            
        return altItem if altItem is not None else self.rootItem # TODO: remove
        #return altItem
        

    def insertChild(self, childItem, position=None, parentIndex=QtCore.QModelIndex()):
        """ Inserts a childItem before row 'position' under the parent index.
        
            If position is None the child will be appended as the last child of the parent.
            Returns the index of the new inserted child.
        """
        parentItem = self.getItem(parentIndex, altItem=self.rootItem)
        
        nChildren = parentItem.childCount()
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
    
    
    def deleteItem(self, itemIndex):
        """ Removes the item at the itemIndex.
        """
        if not itemIndex.isValid():
            logger.debug("No valid item selected for deletion (ignored).")
            return
        
        item = self.getItem(itemIndex, "<no item>")
        logger.debug("Trying to remove {!r}".format(item))
        
        parentIndex = itemIndex.parent()
        #parentItem = self.getItem(parentIndex, altItem=self.rootItem)
        parentItem = self.getItem(parentIndex)
        row = itemIndex.row()
        self.beginRemoveRows(parentIndex, row, row)
        try:
            parentItem.removeChild(row)
        finally:
            self.endRemoveRows()
            