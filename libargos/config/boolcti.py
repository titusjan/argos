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

""" Contains the StringCti and StringCtiEditor classes 
"""
import logging
import numpy as np

from libargos.config.abstractcti import AbstractCti, AbstractCtiEditor
from libargos.qt import Qt, QtGui
from libargos.utils.misc import NOT_SPECIFIED

logger = logging.getLogger(__name__)



class BoolCti(AbstractCti):
    """ Config Tree Item to store an boolean. It can be edited using a check box
    """
    def __init__(self, nodeName, data=NOT_SPECIFIED, defaultData=False):
        """ Constructor. For the parameters see the AbstractCti constructor documentation.
        """
        super(BoolCti, self).__init__(nodeName, data=data, defaultData=defaultData)

    
    def _enforceDataType(self, data):
        """ Converts to bool so that self.data always is of that type.
        """
        return bool(data)
        
        
    @property
    def displayValue(self):
        """ Returns empty string since a checkbox will displayed in the value column instead.  
        """
        return ""
    
   
    @property
    def valueColumnItemFlags(self):
        """ Returns Qt.ItemIsUserCheckable so that a check box will be drawn in the config tree.
            Note that the flags include Qt.ItemIsEditable; this makes the reset button will appear.
        """
        return Qt.ItemIsUserCheckable | Qt.ItemIsEditable
    

    @property
    def checkState(self):
        """ Returns how the checkbox for this cti should look like. Returns None for no checkbox. 
            :rtype: QtCheckState or None 
        """
        if self.data is True:
            return Qt.Checked
        elif self.data is False:
            return Qt.Unchecked
        else:
            raise ValueError("Unexpected data: {!r}".format(self.data))


    @checkState.setter
    def checkState(self, checkState):
        """ Allows the data to be set given a Qt.CheckState.
        """
        if checkState == Qt.Checked:
            self.data = True
        elif checkState == Qt.Unchecked:
            self.data = False
        else:
            raise ValueError("Unexpected check state: {!r}".format(checkState))

    
    def createEditor(self, delegate, parent, _option):
        """ Creates a hidden widget so that only the reset button is visible during editing.
            :type option: QStyleOptionViewItem        
        """
        return EmptyCtiEditor(self, delegate, parent=parent)


        
class EmptyCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a hidden widget so only the reset button is shown. 
    """
    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters 
        """
        super(EmptyCtiEditor, self).__init__(cti, delegate, parent=parent)
        
        # Add hidden widget to store editor value
        self.widget = self.addSubEditor(QtGui.QWidget()) 
        self.widget.hide()
        
    
    def setData(self, data):
        """ Provides the main editor widget with a data to manipulate.
        """
        self.widget.setProperty("editor_data", data)

        
    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.widget.property("editor_data")
        
    