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

""" Contains the IntCti and IntCtiEditor classes 
"""
import logging
import numpy as np

from libargos.config.abstractcti import AbstractCti, AbstractCtiEditor
from libargos.qt import QtGui, QtSlot
from libargos.utils.misc import NOT_SPECIFIED

logger = logging.getLogger(__name__)


class IntCti(AbstractCti):
    """ Config Tree Item to store an integer. It can be edited using a QSpinBox.
    """
    def __init__(self, nodeName, data=NOT_SPECIFIED, defaultData=0, 
                 minValue = None, maxValue = None, stepSize = 1, 
                 specialValueText=None):
        """ Constructor.
            
            :param minValue: minimum data allowed when editing (use None for no minimum)
            :param maxValue: maximum data allowed when editing (use None for no maximum)
            :param stepSize: steps between values when editing (default = 1)
            :param specialValueText: if set, this text will be displayed when the the minValue 
                is selected. It is up to the cti user to interpret this as a special case.            
                    
            For the (other) parameters see the AbstractCti constructor documentation.
        """
        super(IntCti, self).__init__(nodeName, data=data, defaultData=defaultData)
        
        self.minValue = minValue
        self.maxValue = maxValue
        self.stepSize = stepSize
        self.specialValueText = specialValueText
        
    
    def _enforceDataType(self, data):
        """ Converts to int so that this CTI always stores that type. 
        """
        return int(data)
    

    def _dataToString(self, data):
        """ Conversion function used to convert the (default)data to the display value.
        """
        if self.specialValueText is not None and data == self.minValue:
            return self.specialValueText
        else:
            return str(data)    
    
    
    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return ("min = {}, max = {}, step = {}, specVal = {}"
                .format(self.minValue, self.maxValue, self.stepSize, self.specialValueText))
    
    
    def createEditor(self, delegate, parent, option):
        """ Creates a IntCtiEditor. 
            For the parameters see the AbstractCti constructor documentation.
        """
        return IntCtiEditor(self, delegate, parent=parent)
        

        
class IntCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a QSpinbox for editing IntCti objects. 
    """
    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters 
        """
        super(IntCtiEditor, self).__init__(cti, delegate, parent=parent)
        
        spinBox = QtGui.QSpinBox(parent)

        if cti.minValue is None:
            spinBox.setMinimum(np.iinfo('i').min)
        else: 
            spinBox.setMinimum(cti.minValue) 

        if cti.maxValue is None:
            spinBox.setMaximum(np.iinfo('i').max)
        else: 
            spinBox.setMaximum(cti.maxValue) 

        spinBox.setSingleStep(cti.stepSize)
        spinBox.setKeyboardTracking(False)
        
        if cti.specialValueText is not None:
            spinBox.setSpecialValueText(cti.specialValueText)
                    
        self.spinBox = self.addSubEditor(spinBox, isFocusProxy=True)
        self.spinBox.valueChanged.connect(self.commitChangedValue)

        
    def finalize(self):
        """ Called at clean up. Is used to disconnect signals.
        """
        self.spinBox.valueChanged.disconnect(self.commitChangedValue)
        super(IntCtiEditor, self).finalize()

        
    @QtSlot(int)
    def commitChangedValue(self, value):
        """ Commits the new value to the delegate so the inspector can be updated
        """
        #logger.debug("Value changed: {}".format(value))
        self.delegate.commitData.emit(self)
        
    
    def setData(self, data):
        """ Provides the main editor widget with a data to manipulate.
        """
        self.spinBox.setValue(data)

        
    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.spinBox.value()
    