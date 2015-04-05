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

""" Repository tree.

    Currently it supports only selecting one item. That is, the current item is always the 
    selected item. 
    
    The difference between the current item and the selected item(s) is as follows:
    (from: http://doc.qt.digia.com/4.6/model-view-selection.html)
    
    In a view, there is always a current item and a selected item - two independent states. 
    An item can be the current item and selected at the same time. The view is responsible for 
    ensuring that there is always a current item as keyboard navigation, for example, requires 
    a current item.
            
    Current Item:
        There can only be one current item.    
        The current item will be changed with key navigation or mouse button clicks.    
        The current item will be edited if the edit key, F2, is pressed or the item is 
            double-clicked (provided that editing is enabled).    
        The current item is indicated by the focus rectangle.    

    Selected Items:
        There can be multiple selected items.
        The selected state of items is set or unset, depending on several pre-defined modes 
            (e.g., single selection, multiple selection, etc.) when the user interacts with the 
            items.
        The current item can be used together with an anchor to specify a range that should be 
            selected or deselected (or a combination of the two).
        The selected items are indicated with the selection rectangle.
"""
from __future__ import print_function

import logging
from libargos.qt import Qt, QtGui, QtCore, QtSlot
from libargos.widgets.argostreeview import ArgosTreeView
from libargos.repo.repotreemodel import RepoTreeModel
from libargos.widgets.constants import LEFT_DOCK_WIDTH

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901

class RepoTreeView(ArgosTreeView):
    """ Tree widget for browsing the data repository.
    """
    def __init__(self, repoTreeModel):
        """ Constructor
        """
        super(RepoTreeView, self).__init__(repoTreeModel)
 
        treeHeader = self.header()
        treeHeader.resizeSection(RepoTreeModel.COL_NODE_NAME, 180)
        treeHeader.resizeSection(RepoTreeModel.COL_SHAPE, 60)  
        treeHeader.resizeSection(RepoTreeModel.COL_ELEM_TYPE, 60)  
        treeHeader.setStretchLastSection(True)

        headerNames = self.model().horizontalHeaders
        enabled = dict((name, True) for name in headerNames)
        enabled[headerNames[RepoTreeModel.COL_NODE_NAME]] = False # Cannot be unchecked
        checked = dict((name, False) for name in headerNames)
        checked[headerNames[RepoTreeModel.COL_NODE_NAME]] = True 
        checked[headerNames[RepoTreeModel.COL_SHAPE]] = True 
        checked[headerNames[RepoTreeModel.COL_ELEM_TYPE]] = True 
        self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})
        
        # Add actions
        self.topLevelItemActionGroup = QtGui.QActionGroup(self)
        self.topLevelItemActionGroup.setExclusive(False)
        self.currentItemActionGroup = QtGui.QActionGroup(self)
        self.currentItemActionGroup.setExclusive(False)
        
        removeFileAction = QtGui.QAction("Remove File", self.topLevelItemActionGroup, 
                                         shortcut=QtGui.QKeySequence.Delete,  
                                         triggered=self.removeCurrentFile)
        self.addAction(removeFileAction)
        
        reloadFileAction = QtGui.QAction("Reload File", self.currentItemActionGroup, 
                                         shortcut=QtGui.QKeySequence.Refresh,   #"Ctrl+R",  
                                         triggered=self.reloadFileOfCurrentItem)
        self.addAction(reloadFileAction)
        
        openItemAction = QtGui.QAction("Visit Item", self.currentItemActionGroup, 
                                       shortcut="Ctrl+Shift+U", 
                                       triggered=self.openCurrentItem)
        self.addAction(openItemAction)
        
        closeItemAction = QtGui.QAction("Unvisit Item", self.currentItemActionGroup, 
                                        shortcut="Ctrl+U", 
                                        triggered=self.closeCurrentItem)
        self.addAction(closeItemAction)
        
        # Connect signals
        selectionModel = self.selectionModel() # need to store to prevent crash in PySide
        selectionModel.currentChanged.connect(self.updateCurrentItemActions)

        
    def sizeHint(self):
        """ The recommended size for the widget."""
        return QtCore.QSize(LEFT_DOCK_WIDTH, 500)
    
 
    def updateCurrentItemActions(self):
        """ Enables/disables actions when a new item is the current item in the tree view.
        """ 
        currentIndex = self.selectionModel().currentIndex()
        
        # When the model is empty the current index may be invalid.
        hasCurrent = currentIndex.isValid()
        self.currentItemActionGroup.setEnabled(hasCurrent)

        isTopLevel = hasCurrent and self.model().isTopLevelIndex(currentIndex)
        self.topLevelItemActionGroup.setEnabled(isTopLevel)
    
    
    def setCurrentIndex(self, currentIndex):
        """ Sets the current item to be the item at currentIndex.
            Also select the row as to give consistent user feedback.
        """
        selectionModel = self.selectionModel()
        selectionFlags = (QtGui.QItemSelectionModel.ClearAndSelect | 
                          QtGui.QItemSelectionModel.Rows)
        selectionModel.setCurrentIndex(currentIndex, selectionFlags)  


    def _getCurrentIndex(self): # TODO: public?
        """ Returns the index of column 0 of the current item in the repository. 
            See also the notes at the top of this module on current item vs selected item(s).
        """
        selectionModel = self.selectionModel()
        #assert selectionModel.hasSelection(), "No selection"        
        curIndex = selectionModel.currentIndex()
        col0Index = curIndex.sibling(curIndex.row(), 0)
        return col0Index


    def _getCurrentItem(self):
        """ Find the current repo tree item (and the current index while we're at it)
            Returns a tuple with the current item, and its index.
            See also the notes at the top of this module on current item vs selected item(s).
        """
        currentIndex = self._getCurrentIndex()
        currentItem = self.model().getItem(currentIndex)
        return currentItem, currentIndex

    
    @QtSlot()
    def openCurrentItem(self):
        """ Opens the current item in the repository.
        """
        logger.debug("openCurrentItem")
        currentItem, currentIndex = self._getCurrentItem()
        if not currentIndex.isValid():
            return

        currentItem.open()
        self.dataChanged(currentIndex, currentIndex)
        self.expand(currentIndex) # to visit the children and thus show the 'open' icons
         
        
    @QtSlot()
    def closeCurrentItem(self):
        """ Closes the current item in the repository. 
            All its children will be unfetched and closed.
        """
        logger.debug("closeCurrentItem")
        currentItem, currentIndex = self._getCurrentItem()
        if not currentIndex.isValid():
            return

        # First we remove all the children, this will close them as well.
        self.model().removeAllChildrenAtIndex(currentIndex)
        currentItem.close()
        self.dataChanged(currentIndex, currentIndex)
        self.collapse(currentIndex) # otherwise the children will be fetched immediately
                                    # Note that this will happen anyway if the item is e in
                                    # in another view (TODO: what to do about this?)
        
    @QtSlot()
    def removeCurrentFile(self):
        """ Finds the root of of the current item, which represents a file, 
            and removes it from the list.
        """
        logger.debug("removeCurrentFile")
        currentIndex = self._getCurrentIndex()
        if not currentIndex.isValid():
            return

        topLevelIndex = self.model().findTopLevelItemIndex(currentIndex)
        self.model().deleteItemByIndex(topLevelIndex) # this will close the items resources.

    
    @QtSlot()
    def reloadFileOfCurrentItem(self):
        """ Finds the repo tree item that holds the file of the current item and reloads it.
            Reloading is done by removing the repo tree item and inserting a new one.
        """
        logger.debug("reloadFileOfCurrentItem")
        currentIndex = self._getCurrentIndex()
        if not currentIndex.isValid():
            return
        
        fileRtiIndex = self.model().findFileRtiIndex(currentIndex)
        isExpanded = self.isExpanded(fileRtiIndex)
        
        newRtiIndex = self.model().reloadFileAtIndex(fileRtiIndex)
        self.setExpanded(newRtiIndex, isExpanded)
        self.setCurrentIndex(newRtiIndex)
        return newRtiIndex

