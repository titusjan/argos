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
"""
from __future__ import print_function

import logging
from libargos.qt import QtGui, QtCore, QtSlot
from libargos.widgets.argostreeview import ArgosTreeView
from libargos.repo.repotreemodel import RepoTreeModel
from libargos.widgets.constants import (LEFT_DOCK_WIDTH, COL_NODE_NAME_WIDTH, 
                                        COL_SHAPE_WIDTH, COL_ELEM_TYPE_WIDTH)

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901

class RepoTreeView(ArgosTreeView):
    """ Tree widget for browsing the data repository.
    
        Currently it supports only selecting one item. That is, the current item is always the 
        selected item (see notes in ArgosTreeView documentation for details). 
        
    """
    def __init__(self, repoTreeModel, collector, parent=None):
        """ Constructor.
        
            Maintains a reference to a collector. The repo tree view updates the collector when
            the currentIndex changes. 
        """
        super(RepoTreeView, self).__init__(treeModel=repoTreeModel, parent=parent)
 
        self._collector = collector
        
        treeHeader = self.header()
        treeHeader.resizeSection(RepoTreeModel.COL_NODE_NAME, COL_NODE_NAME_WIDTH)
        treeHeader.resizeSection(RepoTreeModel.COL_SHAPE, COL_SHAPE_WIDTH)  
        treeHeader.resizeSection(RepoTreeModel.COL_ELEM_TYPE, COL_ELEM_TYPE_WIDTH)  
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
        selectionModel.currentChanged.connect(self.updateCollector)
        

    def finalize(self):
        """ Disconnects signals and frees resources
        """
        selectionModel = self.selectionModel() # need to store to prevent crash in PySide
        selectionModel.currentChanged.disconnect(self.updateCollector)
        selectionModel.currentChanged.disconnect(self.updateCurrentItemActions)
        
    @property
    def collector(self): # TODO: move to selector class in the future
        """ The collector that this selector view will update. Read only property.
        """
        return self._collector
        
    def sizeHint(self):
        """ The recommended size for the widget."""
        return QtCore.QSize(LEFT_DOCK_WIDTH, 450)
    
 
    @QtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def updateCurrentItemActions(self, currentIndex, _previousIndex):
        """ Enables/disables actions when a new item is the current item in the tree view.
        """ 
        #currentIndex = self.selectionModel().currentIndex()
        
        # When the model is empty the current index may be invalid.
        hasCurrent = currentIndex.isValid()
        self.currentItemActionGroup.setEnabled(hasCurrent)

        isTopLevel = hasCurrent and self.model().isTopLevelIndex(currentIndex)
        self.topLevelItemActionGroup.setEnabled(isTopLevel)
    

    @QtSlot()
    def openCurrentItem(self):
        """ Opens the current item in the repository.
        """
        logger.debug("openCurrentItem")
        _currentIten, currentIndex = self.getCurrentItem()
        if not currentIndex.isValid():
            return
        
        # Expanding the node will visit the children and thus show the 'open' icons
        self.expand(currentIndex) 
         
        
    @QtSlot()
    def closeCurrentItem(self):
        """ Closes the current item in the repository. 
            All its children will be unfetched and closed.
        """
        logger.debug("closeCurrentItem")
        currentItem, currentIndex = self.getCurrentItem()
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
        currentIndex = self.getCurrentIndex()
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
        currentIndex = self.getCurrentIndex()
        if not currentIndex.isValid():
            return
        
        fileRtiIndex = self.model().findFileRtiIndex(currentIndex)
        isExpanded = self.isExpanded(fileRtiIndex)
        
        newRtiIndex = self.model().reloadFileAtIndex(fileRtiIndex)
        self.setExpanded(newRtiIndex, isExpanded)
        self.setCurrentIndex(newRtiIndex)
        return newRtiIndex
    
    
 
    @QtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def updateCollector(self, currentIndex, _previousIndex):
        """ Updates the collector based on the current selection.
        
            A selector always operates on one collector. Each selector implementation will update 
            the collector in its own way. Therefore the selector maintains a reference to the
            collector.
            
            TODO: make Selector classes. For now it's in the RepoTreeView.
        """ 
        # When the model is empty the current index may be invalid.
        hasCurrent = currentIndex.isValid()
        if not hasCurrent:
            return        
        
        rti = self.model().getItem(currentIndex, None)
        assert rti is not None, "sanity check failed. No RTI at current item"
        
        self.collector.updateFromRti(rti)
        #if rti.asArray is not None: # TODO: maybe later
        #    self.collector.updateFromRti(rti)
            
