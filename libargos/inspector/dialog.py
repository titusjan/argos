""" 
    OpenInspectorDialog dialog window that lets the user pick a new inspector.
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import logging

from libargos.qt import QtCore, QtGui, Qt, QtSlot


logger = logging.getLogger(__name__)


# The main window inherits from a Qt class, therefore it has many 
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201 


class OpenInspectorDialog(QtGui.QDialog): 
    """ Dialog window that shows the installed inspector plugins.
    """
    HEADERS = ['Name', 'Library', 'Dimensionality']
    (COL_NAME, COL_LIB, COL_DIM) = range(len(HEADERS))
    
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
        self.table = QtGui.QTableWidget()
        splitter.addWidget(self.table)
        splitter.setCollapsible(0, False)
        
        self.table.setWordWrap(True)
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        #self.table.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        #self.table.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.table.verticalHeader().hide()        
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        
        self.table.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        
        self.table.currentItemChanged.connect(self.currentInspectorChanged)

        tableHeader = self.table.horizontalHeader()
        tableHeader.setDefaultAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        tableHeader.setResizeMode(QtGui.QHeaderView.Interactive) # don't set to stretch
        tableHeader.resizeSection(self.COL_NAME, 250)
        tableHeader.resizeSection(self.COL_LIB, 250)  
        tableHeader.setStretchLastSection(True)

        self.populateTable()                
        
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
        self.table.cellDoubleClicked.connect(self.accept)
        
        splitter.setSizes([300, 150])
        self.resize(QtCore.QSize(800, 600))
        
        
    @property
    def registeredInspectors(self):
        "The inspectors that are registered in the inspector registry"
        return self._registry.registeredInspectors

    
    def currentRegisteredInspector(self):
        """ Returns the RegisteredInspector that is currently selected in the table
        """
        return self.registeredInspectors[self.table.currentRow()]
    
    
    @QtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def currentInspectorChanged(self, _currentIndex=None, _previousIndex=None):
        """ Updates the description text widget when the user clicks on a selector in the table.
            The _currentIndex and _previousIndex parameters are ignored.
        """
        regInt = self.currentRegisteredInspector()
        logger.debug("Selected {}".format(regInt))
        if regInt.descriptionHtml:
            self.editor.setHtml(regInt.descriptionHtml)
        else:
            self.editor.setPlainText(regInt.docString)     
        
        
    def populateTable(self):
        """ Populates the table with the installed inspectors
        """
        table = self.table
        
        table.setUpdatesEnabled(False)
        try:
            table.setRowCount(len(self.registeredInspectors))
            for row, regInt in enumerate(self.registeredInspectors):
                table.setItem(row, self.COL_NAME, QtGui.QTableWidgetItem(regInt.shortName))
                table.setItem(row, self.COL_LIB,  QtGui.QTableWidgetItem(regInt.library))
                table.setItem(row, self.COL_DIM,  QtGui.QTableWidgetItem(str(regInt.nDims)))
        finally:
            table.setUpdatesEnabled(True)
        
        
        

                

