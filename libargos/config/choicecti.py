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

""" Some simple Config Tree Items
"""
import logging

from libargos.config.abstractcti import AbstractCti, AbstractCtiEditor
from libargos.qt import  Qt, QtGui
from libargos.utils.misc import NOT_SPECIFIED


logger = logging.getLogger(__name__)

# Use setIndexWidget()?
 


class ChoiceCti(AbstractCti):
    """ Config Tree Item to store a choice between strings.
    """
    def __init__(self, nodeName, data=NOT_SPECIFIED, defaultData=0, 
                 configValues=None, displayValues=None):
        """ Constructor.
        
            The data and defaultData are integers that are used to store the currentIndex.
            The displayValues parameter must be a list of strings, which will be displayed in the 
            combo box. The _configValues should be a list of the same size with the _configValues
            that each 'choice' represents, e.g. choice 'dashed' maps to configValue Qt.DashLine.
            If displayValues is None, the configValues are used as the displayValues.
                    
            For the (other) parameters see the AbstractCti constructor documentation.
        """
        self._displayValues = [] if displayValues is None else displayValues
        self._configValues = [] if configValues is None else configValues
        assert len(self._configValues) == 0 or len(self._configValues) == len(self._displayValues),\
            "If set, _configValues must have the same length as displayValues."
        
        # Set after self._displayValues are defined. The parent constructor call _enforceDataType
        super(ChoiceCti, self).__init__(nodeName, data=data, defaultData=defaultData)
        
    
    def _enforceDataType(self, data):
        """ Converts to int so that this CTI always stores that type. 
        """
        idx = int(data)
        assert 0 <= idx < len(self._displayValues), \
            "Index should be >= 0 and < {}. Got {}".format(len(self._displayValues), idx)
        return idx

    
    @property
    def configValue(self):
        """ The currently selected configValue
        """
        if self._configValues:
            return self._configValues[self.data]
        else:
            return self._displayValues[self.data]
        
        
    def _dataToString(self, data):
        """ Conversion function used to convert the (default)data to the display value.
        """
        choices = self._displayValues if self._displayValues else self._configValues
        return str(choices[data])
         
            
    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return repr(self._displayValues)
    
    
    def createEditor(self, delegate, parent, option):
        """ Creates a ChoiceCtiEditor. 
            For the parameters see the AbstractCti constructor documentation.
        """
        return ChoiceCtiEditor(self, delegate, parent=parent) 
    
    
        
class ChoiceCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a QCombobox for editing ChoiceCti objects. 
    """
    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters 
        """
        super(ChoiceCtiEditor, self).__init__(cti, delegate, parent=parent)
        
        comboBox = QtGui.QComboBox()
        comboBox.addItems(cti._displayValues)
        
        # Store the configValue in the combo box, although it's not currently used.
        for idx, configValue in enumerate(cti._configValues):
            comboBox.setItemData(idx, configValue, role=Qt.UserRole)
        
        comboBox.activated.connect(self.commitAndClose)
        
        self.comboBox = self.addSubEditor(comboBox, isFocusProxy=True)


    def finalize(self):
        """ Is called when the editor is closed. Disconnect signals.
        """
        self.comboBox.activated.disconnect(self.commitAndClose)
        super(ChoiceCtiEditor, self).finalize()   
        
    
    def setData(self, data):
        """ Provides the main editor widget with a data to manipulate.
        """
        self.comboBox.setCurrentIndex(data)    

        
    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.comboBox.currentIndex()
    
    