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

from libargos.qt.registrytable import RegistryTableModel, RegistryTableView
from libargos.qt import QtCore, QtGui, Qt, QtSlot

logger = logging.getLogger(__name__)

# The main window inherits from a Qt class, therefore it has many 
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201 


class RegistryTab(QtGui.QWidget):
    """ Tab that shows the contents of a single plugin registry.
    
        SIDE EFFECT: will try to import all underlying inspector classes.
            This is done so that error information can be displayed when import was unsuccessful.
    """
    def __init__(self, registry, parent=None, 
                 attrNames=None, headerNames=None, headerSizes=None):
        """ Constructor
        """
        super(RegistryTab, self).__init__(parent=parent)
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
        self.table = RegistryTableView(self.tableModel)
        self.table.sortByColumn(1, Qt.AscendingOrder) # Sort by library by default.
        
        tableHeader = self.table.horizontalHeader()
        for col, headerSize in enumerate(headerSizes):
            if headerSize:
                tableHeader.resizeSection(col, headerSize)
                
        selectionModel = self.table.selectionModel()
        selectionModel.currentRowChanged.connect(self.currentInspectorChanged)
                
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
    
        self.tryImportAllInspectors()
        

    @property
    def registeredInspectors(self):
        "The inspectors that are registered in the inspector registry"
        return self._registry.items

    
    def tryImportAllInspectors(self):
        """ Tries to import all underlying inspector classes
        """ 
        # TODO: update table when importing
        for regItem in self.registeredInspectors:
            if not regItem.triedImport:
                regItem.tryImportClass()
            
    
    def getCurrentRegisteredItem(self):
        """ Returns the inspector that is currently selected in the table. 
            Can return None if there is no data in the table
        """
        return self.table.getCurrentRegisteredItem()
    
    
    @QtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def currentInspectorChanged(self, _currentIndex=None, _previousIndex=None):
        """ Updates the description text widget when the user clicks on a selector in the table.
            The _currentIndex and _previousIndex parameters are ignored.
        """
        self.editor.clear()
        
        regInt = self.getCurrentRegisteredItem()
        logger.debug("Selected {}".format(regInt))
        
        if regInt is None:
            return
        
        if regInt.descriptionHtml:
            self.editor.setHtml(regInt.descriptionHtml)
        else:
            self.editor.setPlainText(regInt.docString)     

        
        
class PluginsDialog(QtGui.QDialog): 
    """ Dialog window that shows the installed inspector plugins.
    
        SIDE EFFECT: will try to import all underlying inspector classes.
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
        
        attrNames = ['identifier', 'fullClassName'] 
        headerSizes = [300, 300]
        
        if inspectorRegistry:
            inspectorTab = RegistryTab(inspectorRegistry, 
                                       attrNames=attrNames, headerSizes=headerSizes)
            self.tabWidget.addTab(inspectorTab, "Inspectors")     
        
        if rtiRegistry:
            rtiTab = RegistryTab(rtiRegistry, 
                                 attrNames=attrNames, headerSizes=headerSizes)
            self.tabWidget.addTab(rtiTab, "File Formats")     

        # Buttons
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)
        layout.addWidget(buttonBox)
        
        self.resize(QtCore.QSize(800, 600))
        
    
    def refresh(self):
        """ Refreshes the tables of all tables by resetting the underlying models
        """
        logger.debug("Resetting: {}".format(self))
        for tabNr in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(tabNr)
            tab.tableModel.reset()
        