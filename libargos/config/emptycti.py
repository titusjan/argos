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

""" Contains the Config and EmptyCtiEditor classes 
"""
import logging

from libargos.config.abstractcti import AbstractCti, AbstractCtiEditor
from libargos.qt import Qt, QtGui
from libargos.utils.misc import NOT_SPECIFIED

logger = logging.getLogger(__name__)



class EmptyCti(AbstractCti):
    """ Read only config Tree Item that only stores None. It can be used to group CTIs
    """
    def __init__(self, nodeName, data=NOT_SPECIFIED, defaultData=None):
        """ Constructor. For the parameters see the AbstractCti constructor documentation.
        """
        super(EmptyCti, self).__init__(nodeName, data=data, defaultData=defaultData)

    
    def _enforceDataType(self, data):
        """ Converts to bool so that self.data always is of that type.
        """
        return data
    
    @property
    def displayValue(self):
        """ Returns empty string since a checkbox will displayed in the value column instead.  
        """
        return ""
   
    @property
    def displayDefaultValue(self):
        """ Returns empty string since a checkbox will displayed in the value column instead.  
        """
        return ""
   
    @property
    def valueColumnItemFlags(self):
        """ Returns Qt.NoItemFlags, the item is not editable.
        """
        return Qt.NoItemFlags # no extra flags
    

        
class EmptyCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a hidden widget. 
        If the item is editable, the reset button is shown. 
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
        
    