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

""" Collector Widget. 
"""
from __future__ import print_function

import logging

from libargos.collect.collectortree import CollectorTree
from libargos.repo.baserti import BaseRti
from libargos.qt import QtGui, QtCore, QtSlot
from libargos.qt.labeledwidget import LabeledWidget
from libargos.utils.cls import check_class, check_is_a_sequence
from libargos.widgets.constants import (TOP_DOCK_HEIGHT)

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901

class Collector(QtGui.QWidget): 
    """ Widget for collecting the selected data. 
        Consists of a tree to collect the VisItems, plus some buttons to add or remove then.
        
        The CollectorTree only stores the VisItems, the intelligence is located in the Collector 
        itself.
    """
    FAKE_DIM_NAME = '-' # The name of the fake dimension with length 1
    FAKE_DIM_IDX  = -999    
    
    def __init__(self):
        """ Constructor
        """
        super(Collector, self).__init__()
        
        self._comboLabels = []  # will be set in clearAndSetComboBoxes
        self._comboBoxes = []   # will be set in clearAndSetComboBoxes
        self.COL_FIRST_COMBO = 1  
        
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.buttonLayout = QtGui.QVBoxLayout()
        self.layout.setContentsMargins(2, 0, 2, 0)
        self.layout.addLayout(self.buttonLayout, stretch=0)
        
        # Add buttons
        self.addVisItemButton = QtGui.QPushButton("Add")
        self.addVisItemButton.setEnabled(False) # not yet implemented
        self.buttonLayout.addWidget(self.addVisItemButton, stretch=0)
        self.removeVisItemButton = QtGui.QPushButton("Remove")
        self.removeVisItemButton.setEnabled(False) # not yet implemented
        self.buttonLayout.addWidget(self.removeVisItemButton, stretch=0)
        self.buttonLayout.addStretch(stretch=1)
        
        # Add tree
        self.tree = CollectorTree(self)
#        self.tree = QtGui.QTreeView()
#        model = QtGui.QStandardItemModel(3, 4)
#        self.tree.setModel(model)
#        treeHeader = self.tree.header()
#        treeHeader.resizeSection(0, 250)         
#        #treeHeader.resizeSection(1, 200)         
        self.layout.addWidget(self.tree)
        
        self.clearAndSetComboBoxes(['X', 'Y'])
        
        
    def sizeHint(self):
        """ The recommended size for the widget."""
        return QtCore.QSize(300, TOP_DOCK_HEIGHT)

    
    @property
    def comboLabels(self):
        """ Returns a copy of the combobox labels (since they are read only) """
        return tuple(self._comboLabels)    

    @property
    def maxCombos(self):
        """ Returns the maximum number of combo boxes """
        return len(self._comboLabels)
    
    
    def clear(self):
        """ Removes all VisItems
        """
        model = self.tree.model()
        # Don't use model.clear(). it will delete the column sizes 
        model.removeRows(0, 1)
        model.setRowCount(1)
        #model.setColumnCount(6)

    
    
    def clearAndSetComboBoxes(self, comboLabels):
        """ Removes all VisItems before setting the new degree.
        """
        check_is_a_sequence(comboLabels)
        row = 0
        self._deleteComboBoxes(row)
        self.clear()
        self._setComboLabels(comboLabels)
        self._createComboBoxes(row)


    def _setComboLabels(self, comboLabels):
        """ Sets the comboLables and updates the headers. Removes old values first. 
        """
        for col, label in enumerate(self._comboLabels, self.COL_FIRST_COMBO):
            self._setHeaderLabel(col, '')
            
        self._comboLabels = comboLabels
        
        for col, label in enumerate(self._comboLabels, self.COL_FIRST_COMBO):
            self._setHeaderLabel(col, label)
            

    def _setHeaderLabel(self, col, text):
        """ Sets the header of column col to text.
            Will increase the number of columns if col is larger than the current number.
        """
        model = self.tree.model()
        item = model.horizontalHeaderItem(col)
        if item:
            item.setText(text)
        else:
            model.setHorizontalHeaderItem(col, QtGui.QStandardItem(text))
            

    @QtSlot(BaseRti)
    def updateFromRti(self, rti):
        """ Updates the current VisItem from the contents of the repo tree item.
        
            Is a slot but the signal is usually connected to the Collector, which then call
            this function directly.
        """
        check_class(rti, BaseRti)
        #assert rti.asArray is not None, "rti must have array" # TODO: maybe later
        
        row = 0
        model = self.tree.model()
        
        # Create path label
        pathItem = QtGui.QStandardItem(rti.nodePath)
        pathItem.setEditable(False)
        model.setItem(row, 0, pathItem)
        
        self._populateComboBoxes(row, rti)
    
        
    def _createComboBoxes(self, row):
        """ Creates a combo box for each of the comboLabels
        """  
        tree = self.tree
        model = self.tree.model()
        
        for col, comboLabel in enumerate(self.comboLabels, self.COL_FIRST_COMBO):
            if col >= model.columnCount():
                model.setColumnCount(col + 1)
                
            logger.debug("Adding combobox at ({}, {})".format(row, col))
            comboBox = QtGui.QComboBox()
            comboBox.addItem("NARF")
            self._comboBoxes.append(comboBox)
            
            editor = LabeledWidget(QtGui.QLabel(comboLabel), comboBox, layoutSpacing=0)
            tree.setIndexWidget(model.index(row, col), editor) 
            

    def _deleteComboBoxes(self, row):
        """ Deletes all comboboxes of a row
        """
        tree = self.tree
        model = self.tree.model()
        
        for col in range(self.COL_FIRST_COMBO, self.maxCombos):
            logger.debug("Removing combobox at: {}, {}".format(row, col))
            tree.setIndexWidget(model.index(row, col), None)
                     
        self._comboBoxes = []
            

    def _populateComboBoxes(self, row, rti):
        """ Populates the comboboxes with values of the repo tree item
        """
        logger.debug("_populateComboBoxes")
        for comboBox in self._comboBoxes:
            comboBox.clear()
            
        if rti.asArray is None:
            return
        
        for comboBoxNr, comboBox in enumerate(self._comboBoxes):
            # Add the 1-length dimension
            comboBox.addItem(self.FAKE_DIM_NAME, userData = self.FAKE_DIM_IDX)
            
            for dimNr in range(rti.asArray.ndim):
                comboBox.addItem("Dim{}".format(dimNr), userData=dimNr)
                        
                # We set the nth combo-box index to the last item - n. This because the 
                # NetCDF-CF conventions have the preferred dimension order of T, Z, Y, X. 
                comboBox.setCurrentIndex(max(0, rti.asArray.ndim - comboBoxNr))
            
                
                                    
                    
            