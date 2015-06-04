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
    OpenInspectorDialog dialog window that lets the user pick a new inspector.
"""
from __future__ import print_function

import logging

from libargos.qt.registrytable import RegistryTableModel, RegistryTableView
from libargos.qt import QtCore, QtGui, Qt, QtSlot


logger = logging.getLogger(__name__)


# The main window inherits from a Qt class, therefore it has many 
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201 

class OpenInspectorDialog(QtGui.QDialog): 
    """ Dialog window that shows the installed inspector plugins.
    
        SIDE EFFECT: will try to import all underlying inspector classes.
            This is done so that help and number of dimensions can be displayed.
    """

    def __init__(self, registry, parent=None):
        """ Constructor
        """
        super(OpenInspectorDialog, self).__init__(parent=parent)

        self._registry = registry
                
        self.setModal(True)
        layout = QtGui.QVBoxLayout(self)
        splitter = QtGui.QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Table        
        attrNames = ('name', 'library', 'nDims')
        self.tableModel = RegistryTableModel(self._registry, attrNames=attrNames, parent=self)
        self.table = RegistryTableView(self.tableModel)
        self.table.sortByColumn(1, Qt.AscendingOrder) # Sort by library by default.
        
        tableHeader = self.table.horizontalHeader()
        tableHeader.resizeSection(0, 250)
        tableHeader.resizeSection(1, 250)
                
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
        self.editor.setPlainText("Inspector info...")        
        splitter.addWidget(self.editor)
        splitter.setCollapsible(1, False) # True?
        
        # Buttons
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                           QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)
        
        # Double clicking is equivalent to selecting it and clicking Ok.
        self.table.doubleClicked.connect(self.accept)
        
        splitter.setSizes([300, 150])
        self.resize(QtCore.QSize(800, 600))
        
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
        
        