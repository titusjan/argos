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

""" Contains the FloatCti and FloatCtiEditor classes 
"""
import logging
import numpy as np

from libargos.config.abstractcti import AbstractCti, AbstractCtiEditor
from libargos.qt import QtGui
from libargos.utils.misc import NOT_SPECIFIED

logger = logging.getLogger(__name__)


class FloatCti(AbstractCti):
    """ Config Tree Item to store a floating point number. It can be edited using a QDoubleSpinBox.
    """
    def __init__(self, nodeName, data=NOT_SPECIFIED, defaultData=0, 
                 minValue = None, maxValue = None, stepSize = 1.0, decimals = 2):
        """ Constructor.
            
            :param minValue: minimum data allowed when editing (use None for no minimum)
            :param maxValue: maximum data allowed when editing (use None for no maximum)
            :param stepSize: steps between values when editing (default = 1)
            :param decimals: Sets how many decimals the spin box will use for displaying.
                Note: The maximum, minimum and value might change as a result of changing this.
                    
            For the (other) parameters see the AbstractCti constructor documentation.
        """
        super(FloatCti, self).__init__(nodeName, data=data, defaultData=defaultData)
        
        self.decimals = decimals 
        self.minValue = minValue
        self.maxValue = maxValue
        self.stepSize = stepSize
    
        
    def _enforceDataType(self, data):
        """ Converts to int so that this CTI always stores that type. 
        """
        return float(data)
    
    @property
    def displayValue(self):
        """ The string representation of the data"""
        return "{:.{decimals}f}".format(self.data, decimals=self.decimals)
    
    @property
    def displayDefaultValue(self):
        """ The string representation of the default data"""
        return "{:.{decimals}f}".format(self.defaultData, decimals=self.decimals)
        
    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return "min = {}, max = {}, step = {}".format(self.minValue, self.maxValue, self.stepSize)
    
    
    def createEditor(self, delegate, parent, option):
        """ Creates a IntCtiEditor. 
            For the parameters see the AbstractCti constructor documentation.
        """
        return FloatCtiEditor(self, delegate, parent=parent, 
                              minValue=self.minValue, maxValue=self.maxValue, 
                              stepSize=self.stepSize, decimals=self.decimals)
        

        
class FloatCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a QDoubleSpinbox for editing FloatCti objects. 
    """
    def __init__(self, cti, delegate, parent=None, 
                 minValue = None, maxValue = None, # TODO: why separate min/maxValue parameters?
                 stepSize = 1.0, decimals=2):
        """ See the AbstractCtiEditor for more info on the parameters 
        """
        super(FloatCtiEditor, self).__init__(cti, delegate, parent=parent)
        
        spinBox = QtGui.QDoubleSpinBox(parent)

        if minValue is None:
            spinBox.setMinimum(np.finfo('d').min)
        else: 
            spinBox.setMinimum(minValue) 

        if maxValue is None:
            spinBox.setMaximum(np.finfo('d').max)
        else: 
            spinBox.setMaximum(maxValue) 

        spinBox.setSingleStep(stepSize)
        spinBox.setDecimals(decimals)

        self.spinBox = self.addSubEditor(spinBox, isFocusProxy=True)
        
    
    def setData(self, data):
        """ Provides the main editor widget with a data to manipulate.
        """
        self.spinBox.setValue(data)

        
    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.spinBox.value()
    