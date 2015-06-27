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

""" Contains the Config and GroupCtiEditor classes 
"""
import logging

from libargos.config.abstractcti import AbstractCti
from libargos.config.groupcti import GroupCtiEditor
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
        return GroupCtiEditor(self, delegate, parent=parent)

