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

""" 
    PluginsDialog window that shows which plugins are registered.
"""
from __future__ import print_function

import logging

from libargos.qt.registry import ClassRegItem
from libargos.qt.registrytable import RegistryTableModel, RegistryTableView
from libargos.qt.registrytable import QCOLOR_REGULAR, QCOLOR_NOT_IMPORTED, QCOLOR_ERROR
from libargos.qt import QtCore, QtGui, Qt, QtSlot
from libargos.utils.cls import check_class

logger = logging.getLogger(__name__)

# The main window inherits from a Qt class, therefore it has many 
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201 


class RegistryTab(QtGui.QWidget):
    """ Tab that shows the contents of a single plugin registry.
    
        SIDE EFFECT: will try to import all underlying classes.
            This is done so that error information can be displayed when import was unsuccessful.
    """
    def __init__(self, registry, parent=None, 
                 attrNames=None, headerNames=None, headerSizes=None, 
                 onlyShowImported=False):
        """ Constructor.
        
            If onlyShowImported == True, regItems that are not (successfully) imported are 
            filtered from the table.
        """
        super(RegistryTab, self).__init__(parent=parent)
        self._onlyShowImported = onlyShowImported
        self._registry = registry
        
        attrNames = [] if attrNames is None else attrNames
        headerNames = attrNames if headerNames is None else headerNames
        headerSizes = [] if headerSizes is None else headerSizes 
        if headerSizes is None:
            headerSizes = []
        else:
            assert len(headerSizes) == len(attrNames), \
                "Size mismatch {} != {}".format(len(headerSizes), len(attrNames))

        layout = QtGui.QVBoxLayout(self)
        splitter = QtGui.QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Table
        self.tableModel = RegistryTableModel(self._registry, attrNames=attrNames, parent=self)
        self.table = RegistryTableView(self.tableModel, onlyShowImported=self.onlyShowImported)
        
        tableHeader = self.table.horizontalHeader()
        for col, headerSize in enumerate(headerSizes):
            if headerSize:
                tableHeader.resizeSection(col, headerSize)
                
        selectionModel = self.table.selectionModel()
        selectionModel.currentRowChanged.connect(self.currentItemChanged)
                
        splitter.addWidget(self.table)
        splitter.setCollapsible(0, False)
        
        # Detail info widget
        font = QtGui.QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(13)

        self.editor = QtGui.QTextEdit()
        self.editor = QtGui.QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setFont(font)
        self.editor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.editor.clear()      
        splitter.addWidget(self.editor)
        splitter.setCollapsible(1, False) # True?
        splitter.setSizes([300, 150])
    
        self.tryImportAllPlugins()
        

    @property
    def onlyShowImported(self):
        "If True, regItems that are not (successfully) imported are filtered from in the table"
        return self._onlyShowImported
            

    @property
    def registeredItems(self):
        "Returns the items from the registry"
        return self._registry.items

    
    def tryImportAllPlugins(self):
        """ Tries to import all underlying plugin classes
        """ 
        logger.debug("Importing all plugins in the registry: {}".format(self._registry))
        
        self.tableModel.beginResetModel()
        try:
            for regItem in self.registeredItems:
                if not regItem.triedImport:
                    regItem.tryImportClass()
        finally:
            self.tableModel.endResetModel()
            
        logger.debug("Importing finished.")            
            
    
    def getCurrentRegItem(self):
        """ Returns the item that is currently selected in the table. 
            Can return None if there is no data in the table
        """
        return self.table.getCurrentRegItem()
    
    
    def setCurrentRegItem(self, regItem):
        """ Returns the item that is currently selected in the table. 
            Can return None if there is no data in the table
        """
        check_class(regItem, ClassRegItem, allow_none=True)
        return self.table.setCurrentRegItem(regItem)
    
    
    @QtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def currentItemChanged(self, _currentIndex=None, _previousIndex=None):
        """ Updates the description text widget when the user clicks on a selector in the table.
            The _currentIndex and _previousIndex parameters are ignored.
        """
        self.editor.clear()
        self.editor.setTextColor(QCOLOR_REGULAR)
        
        regItem = self.getCurrentRegItem()

        if regItem is None:
            return
        
        if regItem.successfullyImported is None:
            self.editor.setTextColor(QCOLOR_NOT_IMPORTED)
            self.editor.setPlainText('<plugin not yet imported>')     
        elif regItem.successfullyImported is False:   
            self.editor.setTextColor(QCOLOR_ERROR)
            self.editor.setPlainText(str(regItem.exception))     
        elif regItem.descriptionHtml:
            self.editor.setHtml(regItem.descriptionHtml)
        else:
            self.editor.setPlainText(regItem.docString)     

        
        
class PluginsDialog(QtGui.QDialog): 
    """ Dialog window that shows the installed plugins.
    
        SIDE EFFECT: will try to import all underlying classes.
            This is done so that error information can be displayed when import was unsuccessful.
    """

    def __init__(self, 
                 inspectorRegistry=None, 
                 rtiRegistry=None, 
                 parent=None):
        """ Constructor
        """
        super(PluginsDialog, self).__init__(parent=parent)

        self.setWindowTitle("Installed Argos Plugins")
        self.setModal(False)

        layout = QtGui.QVBoxLayout(self)
        
        self.tabWidget = QtGui.QTabWidget()
        layout.addWidget(self.tabWidget)
        
        attrNames = ['fullName', 'fullClassName', 'pythonPath'] 
        headerSizes = [200, 300, None]
        
        if inspectorRegistry:
            inspectorTab = RegistryTab(inspectorRegistry, 
                                       attrNames=attrNames, headerSizes=headerSizes)
            self.tabWidget.addTab(inspectorTab, "Inspectors")     
        
        if rtiRegistry:
            rtiTab = RegistryTab(rtiRegistry, 
                                 attrNames=attrNames, headerSizes=headerSizes)
            self.tabWidget.addTab(rtiTab, "File Formats")     

        # Sort by fullName by default.
        for tabNr in range(self.tabWidget.count()):
            self.tabWidget.widget(tabNr).table.sortByColumn(0, Qt.AscendingOrder) 

        # Buttons
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)
        layout.addWidget(buttonBox)
        
        self.resize(QtCore.QSize(1100, 700))
        
    
    def tryImportAllPlugins(self):
        """ Refreshes the tables of all tables by importing the underlying classes
        """
        logger.debug("Resetting: {}".format(self))
        for tabNr in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(tabNr)
            tab.tryImportAllPlugins()
            
            