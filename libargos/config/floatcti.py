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
from libargos.qt import QtGui, QtSlot
from libargos.qt.scientificspinbox import ScientificDoubleSpinBox

logger = logging.getLogger(__name__)


class FloatCti(AbstractCti):
    """ Config Tree Item to store a floating point number. It can be edited using a QDoubleSpinBox.
    """
    def __init__(self, nodeName, defaultData=0, 
                 minValue = None, maxValue = None, stepSize = 1.0, decimals = 2, 
                 specialValueText=None):
        """ Constructor.
            
            :param minValue: minimum data allowed when editing (use None for no minimum)
            :param maxValue: maximum data allowed when editing (use None for no maximum)
            :param stepSize: steps between values when editing (default = 1)
            :param decimals: Sets how many decimals the spin box will use for displaying.
                Note: The maximum, minimum and value might change as a result of changing this.
            :param specialValueText: if set, this text will be displayed when the the minValue 
                is selected. It is up to the cti user to interpret this as a special case.
                    
            For the (other) parameters see the AbstractCti constructor documentation.
        """
        super(FloatCti, self).__init__(nodeName, defaultData)
        
        self.decimals = decimals 
        self.minValue = minValue
        self.maxValue = maxValue
        self.stepSize = stepSize
        self.specialValueText = specialValueText
    
        
    def _enforceDataType(self, data):
        """ Converts to int so that this CTI always stores that type. 
        """
        return float(data)
    
    
    def _dataToString(self, data):
        """ Conversion function used to convert the (default)data to the display value.
        """
        if self.specialValueText is not None and data == self.minValue:
            return self.specialValueText
        else:
            return "{:.{precission}f}".format(data, precission=self.decimals)
        
        
    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return ("min = {}, max = {}, step = {}, decimals = {}, specVal = {}"
                .format(self.minValue, self.maxValue, self.stepSize, 
                        self.decimals, self.specialValueText))
    
    
    def createEditor(self, delegate, parent, option):
        """ Creates a FloatCtiEditor. 
            For the parameters see the AbstractCti constructor documentation.
        """
        return FloatCtiEditor(self, delegate, parent=parent)
        

        
class FloatCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a QDoubleSpinbox for editing FloatCti objects. 
    """
    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters 
        """
        super(FloatCtiEditor, self).__init__(cti, delegate, parent=parent)
        
        spinBox = QtGui.QDoubleSpinBox(parent)

        if cti.minValue is None:
            spinBox.setMinimum(np.finfo('d').min)
        else: 
            spinBox.setMinimum(cti.minValue) 

        if cti.maxValue is None:
            spinBox.setMaximum(np.finfo('d').max)
        else: 
            spinBox.setMaximum(cti.maxValue) 

        spinBox.setSingleStep(cti.stepSize)
        spinBox.setDecimals(cti.decimals)
        spinBox.setKeyboardTracking(False)
        
        if cti.specialValueText is not None:
            spinBox.setSpecialValueText(cti.specialValueText)

        self.spinBox = self.addSubEditor(spinBox, isFocusProxy=True)
        self.spinBox.valueChanged.connect(self.commitChangedValue)

        
    def finalize(self):
        """ Called at clean up. Is used to disconnect signals.
        """
        self.spinBox.valueChanged.disconnect(self.commitChangedValue)
        super(FloatCtiEditor, self).finalize()
        
        
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



class SnFloatCti(AbstractCti):
    """ Config Tree Item to store a floating point number. It can be edited using a QDoubleSpinBox.
    """
    def __init__(self, nodeName, defaultData=0,
                 minValue = None, maxValue = None, decimals = 2,
                 specialValueText=None):
        """ Constructor.

            :param minValue: minimum data allowed when editing (use None for no minimum)
            :param maxValue: maximum data allowed when editing (use None for no maximum)
            :param decimals: Sets how many decimals the spin box will use for displaying.
                Note: The maximum, minimum and value might change as a result of changing this.
            :param specialValueText: if set, this text will be displayed when the the minValue
                is selected. It is up to the cti user to interpret this as a special case.

            For the (other) parameters see the AbstractCti constructor documentation.
        """
        super(SnFloatCti, self).__init__(nodeName, defaultData)

        self.decimals = decimals
        self.minValue = minValue
        self.maxValue = maxValue

        self.specialValueText = specialValueText


    @property
    def precision(self):
        """ Returns precision used in the string formatting. I.e. {:{width}.{precision}g)}
            When using the :g format, the following holds, decimals = precision - 1. Therefore
            this property returns self.decimals - 1.
            See https://docs.python.org/2/library/string.html#format-specification-mini-language
        """
        return self.decimals + 1


    def _enforceDataType(self, data):
        """ Converts to int so that this CTI always stores that type.
        """
        return float(data)


    def _dataToString(self, data):
        """ Conversion function used to convert the (default)data to the display value.
        """
        if self.specialValueText is not None and data == self.minValue:
            return self.specialValueText
        else:
            # See
            return "{:.{precission}e}".format(data, precission=self.precision)


    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return ("min = {}, max = {}, decimals = {}, specVal = {}"
                .format(self.minValue, self.maxValue,
                        self.decimals, self.specialValueText))


    def createEditor(self, delegate, parent, option):
        """ Creates a FloatCtiEditor.
            For the parameters see the AbstractCti constructor documentation.
        """
        return SnFloatCtiEditor(self, delegate, self.precision, parent=parent)



class SnFloatCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a ScientificDoubleSpinBox for editing FloatCti objects.
    """
    def __init__(self, cti, delegate, precision, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters
        """
        super(SnFloatCtiEditor, self).__init__(cti, delegate, parent=parent)

        spinBox = ScientificDoubleSpinBox(precision=precision, parent=parent)

        if cti.minValue is None:
            spinBox.setMinimum(np.finfo('d').min)
        else:
            spinBox.setMinimum(cti.minValue)

        if cti.maxValue is None:
            spinBox.setMaximum(np.finfo('d').max)
        else:
            spinBox.setMaximum(cti.maxValue)

        spinBox.setKeyboardTracking(False)

        if cti.specialValueText is not None:
            spinBox.setSpecialValueText(cti.specialValueText)

        self.spinBox = self.addSubEditor(spinBox, isFocusProxy=True)
        self.spinBox.valueChanged.connect(self.commitChangedValue)


    def finalize(self):
        """ Called at clean up. Is used to disconnect signals.
        """
        self.spinBox.valueChanged.disconnect(self.commitChangedValue)
        super(SnFloatCtiEditor, self).finalize()


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
        self.spinBox.selectAll()


    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.spinBox.value()
