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
    
    def __init__(self):
        """ Constructor
        """
        super(Collector, self).__init__()
        
        self._comboLabels = ['X', 'Y']
        
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.buttonLayout = QtGui.QVBoxLayout(self)
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
        
        
    def sizeHint(self):
        """ The recommended size for the widget."""
        return QtCore.QSize(300, TOP_DOCK_HEIGHT)

    def clear(self):
        """ Removes all VisItems
        """
        self.tree.model().clear()
    
    def clearAndSetComboLabels(self, comboLabels):
        """ Removes all VisItems before setting the new degree.
        """
        check_is_a_sequence(comboLabels)
        self.clear()
        self._comboLabels = comboLabels
    
    @property
    def comboLabels(self):
        """ Returns a copy of the combobox labels (since they are read only) """
        return tuple(self._comboLabels)    

    @property
    def maxCombos(self):
        """ Returns the maximum number of combo boxes """
        return len(self._comboLabels)



    @QtSlot(BaseRti)
    def updateFromRti(self, rti):
        """ Updates the current VisItem from the contents of the repo tree item.
        
            Is a slot but the signal is usually connected to the Collector, which then call
            this function directly.
        """
        check_class(rti, BaseRti)
        assert rti.asArray is not None, "rti must have array"
        
        row = 0
        model = self.tree.model()
        
        # Delete current widgets
        self._deleteComboBoxes(row)
        
        # Create path label
        pathItem = QtGui.QStandardItem(rti.nodePath)
        pathItem.setEditable(False)
        model.setItem(row, 0, pathItem)
        
        self._createComboBoxesFromRti(rti, row)
    
        
    def _createComboBoxesFromRti(self, rti, row):
        """ Creates a combo boxe for each of the comboLabel
        """  
        tree = self.tree
        model = self.tree.model()
        
        for idx, comboLabel in enumerate(self.comboLabels):
            col = idx + 1 # first col is label
            if col >= model.columnCount():
                model.setColumnCount(col + 1)
                
            logger.debug("adding combobox at {} {}".format(row, col))

            comboBox = QtGui.QComboBox()
            for dimNr in range(rti.asArray.ndim):
                comboBox.addItem("Dim{}".format(dimNr))

            editor = LabeledWidget(QtGui.QLabel(comboLabel), comboBox, layoutSpacing=0)
            tree.setIndexWidget(model.index(row, col), editor) 
        
        
    def _deleteComboBoxes(self, row):
        """ Deletes all comboboxes of a row
        """
        tree = self.tree
        model = self.tree.model()
        
        for idx in range(self.maxCombos):
            col = idx + 1 # first col is label
            logger.debug("Removing editor at: {}, {}".format(row, col))
            tree.setIndexWidget(model.index(row, col), QtGui.QFrame())         
            #model.setItem(row, col, QtGui.QStandardItem('...'))
