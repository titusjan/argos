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

import logging, os
from libargos.qt import QtCore, QtGui, Qt, QtSlot
from libargos.qt.togglecolumn import ToggleColumnTreeView

from libargos.state.commonstate import getCommonState
from libargos.repo.memoryrti import ScalarRti
from libargos.repo.filesytemrti import UnknownFileRti, DirectoryRti


logger = logging.getLogger(__name__)

class RepoTree(ToggleColumnTreeView):
    """ Tree widget for browsing the data repository.
    """
    def __init__(self, repoTreeModel):
        """ Constructor
        """
        super(RepoTree, self).__init__()
        self.setModel(repoTreeModel)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems) # TODO: SelectRows
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.setAnimated(True)
        self.setAllColumnsShowFocus(True) 

        treeHeader = self.header()
        treeHeader.setMovable(True)
        treeHeader.setStretchLastSection(False)  
        treeHeader.resizeSection(0, 200)
        headerNames = self.model().horizontalHeaders
        enabled = dict((name, True) for name in headerNames)
        enabled[headerNames[0]] = False # Fist column cannot be unchecked
        self.addHeaderContextMenu(enabled=enabled, checkable={})

        
    def loadRepoTreeItem(self, repoTreeItem, expand=False):
        """ Loads a tree item in the repository and expands it.
        """
        assert repoTreeItem._parentItem is None, "repoTreeItem {!r}".format(repoTreeItem)
        storeRootIndex = self.model().insertItem(repoTreeItem)
        self.setExpanded(storeRootIndex, expand)


    def loadFile(self, fileName, expand=False):
        """ Loads a file in the repository. Autodetects the RTI type needed
        """
        repoTreeItem = self._autodetectedRepoTreeItem(fileName)
        self.loadRepoTreeItem(repoTreeItem, expand=expand)
        
                
    def _autodetectedRepoTreeItem(self, fileName):
        """ Determines the type of RepoTreeItem to use given a file name.
            Temporary solution
        """
        _, extension = os.path.splitext(fileName)
        if os.path.isdir(fileName):
            cls = DirectoryRti
        else:
            try:
                cls = getCommonState().registry.getRtiByExtension(extension)
            except KeyError:
                cls = UnknownFileRti
        return cls.createFromFileName(fileName)
        
        
    def _getSelectedItemIndex(self):
        """ Returns the index of the selected item in the repository. 
        """
        selectionModel = self.selectionModel()
        assert selectionModel.hasSelection(), "No selection"        
        curIndex = selectionModel.currentIndex()
        col0Index = curIndex.sibling(curIndex.row(), 0)
        return col0Index


    def _getSelectedItem(self):
        """ Returns a tuple with the selected item, and its index, in the repository. 
        """
        selectedIndex = self._getSelectedItemIndex()
        selectedItem = self.model().getItem(selectedIndex)
        return selectedItem, selectedIndex


    
    def openSelectedItem(self):
        """ Opens the selected file in the repository. The file must be closed beforehand.
        """
        selectedItem, _selectedIndex = self._getSelectedItem()
        selectedItem.open()
         

    def closeSelectedItem(self):
        """ Closes the selected file in the repository. The file must be closed beforehand.
        """
        _selectedItem, selectedIndex = self._getSelectedItem()
        self.model().removeAllChildrenAtIndex(selectedIndex)
        self.collapse(selectedIndex) # otherwise the children will be fetched immediately
        
    
#    def openSelectedFile(self):
#        """ Opens the selected item repository.
#        """
#        logger.debug("openSelectedFile")
#        
#        selectedItem, selectedIndex = self._getSelectedItem()
#        if not isinstance(selectedItem, FileRtiMixin):
#            logger.warn("Cannot open item of type (ignored): {}".format(type(selectedItem)))
#            return
#
#        openFileItem = self._autodetectedRepoTreeItem(selectedItem.fileName)
#        insertedIndex = self.model().replaceItemAtIndex(openFileItem, selectedIndex)
#        self.selectionModel().setCurrentIndex(insertedIndex, 
#                                              QtGui.QItemSelectionModel.ClearAndSelect)
#        logger.debug("selectedFile opened")
#         
#
#    def closeSelectedFile(self):
#        """ Opens the selected file in the repository. The file must be closed beforehand.
#        """
#        logger.debug("closeSelectedFile")
#        
#        selectedItem, selectedIndex = self._getSelectedItem()
#        if not isinstance(selectedItem, FileRtiMixin):
#            logger.warn("Cannot close item of type (ignored): {}".format(type(selectedItem)))
#            return
#        
#        #selectedItem.closeFile()
#        selectedItem.finalize()
#
#        openFileItem = UnknownFileRti(fileName=selectedItem.fileName, nodeName=selectedItem.nodeName)
#        insertedIndex = self.model().replaceItemAtIndex(openFileItem, selectedIndex)
#        self.selectionModel().setCurrentIndex(insertedIndex, 
#                                              QtGui.QItemSelectionModel.ClearAndSelect)
#        logger.debug("selectedFile closed")
        
    @QtSlot()
    def insertItemAtSelection(self):
        """ Temporary test method
        """
        import random
        col0Index = self._getSelectedItemIndex()

        value = random.randint(20, 99)
        model = self.model()
        childIndex = model.insertItem(ScalarRti("new child", str(value)), 
                                      parentIndex = col0Index)
        self.selectionModel().setCurrentIndex(childIndex, 
                                              QtGui.QItemSelectionModel.ClearAndSelect)
        
        newChildItem = model.getItem(childIndex, altItem=model.rootItem)
        logger.debug("Added child: {} under {}".format(newChildItem, newChildItem.parentItem))

        #self.updateActions() # TODO: needed?        
        
        
    @QtSlot()    
    def removeSelectedRow(self):
        """ Temporary test method
        """
        logger.debug("RemoveRow()")
        selectionModel = self.selectionModel()
        assert selectionModel.hasSelection(), "No selection"
        self.model().deleteItemByIndex(selectionModel.currentIndex()) # TODO: repository close
        logger.debug("removeSelectedRow completed")        
            
        
