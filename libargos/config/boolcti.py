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




class TriBoolCti(AbstractCti):
    """ Config Tree Item to store a nullable boolean (True, False or None).
     
        It can be edited using a tri-state check box. However, the user can not set the value
        to partially checked directly, it will only be partially checked if some of its children
        are checked and others are not! This is a bug/feature of Qt.
        See: https://bugreports.qt.io/browse/QTBUG-7674 and 
             http://comments.gmane.org/gmane.comp.lib.qt.general/925
    """
    def __init__(self, nodeName, data=NOT_SPECIFIED, defaultData=False):
        """ Constructor. For the parameters see the AbstractCti constructor documentation.
        """
        super(TriBoolCti, self).__init__(nodeName, data=data, defaultData=defaultData)

    
    def _enforceDataType(self, data):
        """ Converts to bool so that self.data always is of that type.
        """
        return None if data is None else bool(data)
        
        
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
        return Qt.ItemIsTristate | Qt.ItemIsUserCheckable | Qt.ItemIsEditable
    

    @property
    def checkState(self):
        """ Returns how the checkbox for this cti should look like. Returns None for no checkbox. 
            :rtype: QtCheckState or None 
        """
        #logger.debug("checkState getter: data = {}".format(self.data))
        if self.data is True:
            return Qt.Checked
        elif self.data is False:
            return Qt.Unchecked
        elif self.data is None:
            return Qt.PartiallyChecked
        else:
            raise ValueError("Unexpected data: {!r}".format(self.data))


    @checkState.setter
    def checkState(self, checkState):
        """ Allows the data to be set given a Qt.CheckState.
        """
        logger.debug("checkState setter: {}".format(checkState))
        if checkState == Qt.Checked:
            self.data = True
        elif checkState == Qt.Unchecked:
            self.data = False
        elif checkState == Qt.PartiallyChecked:
            # This never occurs, see remarks above in the classes' docstring
            assert False, "This never happens. Please report if it does."
            self.data = None
        else:
            raise ValueError("Unexpected check state: {!r}".format(checkState))

    
    def createEditor(self, delegate, parent, _option):
        """ Creates a hidden widget so that only the reset button is visible during editing.
            :type option: QStyleOptionViewItem        
        """
        return GroupCtiEditor(self, delegate, parent=parent)

