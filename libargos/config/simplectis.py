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
import numpy as np

from .basecti import BaseCti, USE_DEFAULT_VALUE
from libargos.qt import QtGui


logger = logging.getLogger(__name__)

        
    
# TODO: FloatCti using QDoubleSpinBox
# TODO: Bool and CombiBox  
# TODO: Color selector

# TODO: what about None's


class StringCti(BaseCti):
    """ Config Tree Item to store a string. It can be edited with a QLineEdit
        The string can have an optional maximum length.
    """
    def __init__(self, nodeName='', value=USE_DEFAULT_VALUE, defaultValue='', 
                 maxLength=None):
        """ Constructor
            :param maxLength: maximum length of the string
        """
        super(StringCti, self).__init__(nodeName=nodeName, value=value, defaultValue=defaultValue)
        
        # We could define a mask here as well but since that very likely will be rarely used, 
        # we don't want to store it for each cti. You can make a subclass if you need it. 
        self.maxLength = maxLength


    def _convertValueType(self, value):
        """ Converts to str so that this CTI always stores that type. 
        """
        return str(value)    
        
    
    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return "maxLength = {}".format(self.maxLength)
    
    
    def createEditor(self, _option):
        """ Creates an editor (QWidget) for editing. 
            It's parent will be set by the ConfigItemDelegate class
            :param option: describes the parameters used to draw an item in a view widget.
            :type option: QStyleOptionViewItem
        """
        editor = QtGui.QLineEdit()
        if self.maxLength is not None:
            editor.setMaxLength(self.maxLength)
        return editor
        
        
    def setEditorValue(self, editor, value):
        """ Provides the editor widget with a value to manipulate.
            
            The value parameter could be replaced by self.value but the caller 
            (ConfigItemelegate.getModelData) retrieves it via the model to be consistent 
            with setModelData.
             
            :type editor: QWidget
        """
        lineEditor = editor
        lineEditor.setText(value)
        
        
    def getEditorValue(self, editor):
        """ Gets data from the editor widget.
            
            :type editor: QWidget
        """
        lineEditor = editor
        return lineEditor.text()



class IntegerCti(BaseCti):
    """ Config Tree Item to store an integer. It can be edited using a QSinBox.
    """
    def __init__(self, nodeName='', value=USE_DEFAULT_VALUE, defaultValue=0, 
                 minValue = None, maxValue = None, stepSize = 1):
        """ Constructor
            :param nodeName: name of this node (used to construct the node path).
            :param value: the configuration value. If omitted the defaultValue will be used.
            :param defaultValue: default value to which the value can be reset or initialized
                if omitted  from the constructor
        """
        super(IntegerCti, self).__init__(nodeName=nodeName, value=value, defaultValue=defaultValue)
        
        self.minValue = minValue
        self.maxValue = maxValue
        self.stepSize = stepSize

    
    def _convertValueType(self, value):
        """ Converts to int so that this CTI always stores that type. 
        """
        return int(value)
        
    
    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return "min = {}, max = {}, step = {}".format(self.minValue, self.maxValue, self.stepSize)
    
    
    def createEditor(self, _option):
        """ Creates a spinbox for editing. 
            :type option: QStyleOptionViewItem
        """
        spinBox = QtGui.QSpinBox()

        if self.minValue is None:
            spinBox.setMinimum(np.iinfo('i').min)
        else: 
            spinBox.setMinimum(self.minValue) 

        if self.maxValue is None:
            spinBox.setMaximum(np.iinfo('i').max)
        else: 
            spinBox.setMaximum(self.maxValue) 

        spinBox.setSingleStep(self.stepSize)
        return spinBox
        
        
    def setEditorValue(self, spinBox, value):
        """ Provides the spinBox editor widget with a value to manipulate.
        """
        spinBox.setValue(value)
        
        
    def getEditorValue(self, spinBox):
        """ Gets data from the spinbox editor widget.
            
            :type editor: QWidget
        """
        spinBox.interpretText()
        value = spinBox.value()
        return value




class BoolCti(BaseCti):
    """ Config Tree Item to store an integer. It can be edited using a QSinBox.
    """
    def __init__(self, nodeName='', value=USE_DEFAULT_VALUE, defaultValue=None):
        """ Constructor
            :param nodeName: name of this node (used to construct the node path).
            :param value: the configuration value. If omitted the defaultValue will be used.
            :param defaultValue: default value to which the value can be reset or initialized
                if omitted  from the constructor
        """
        super(IntegerCti, self).__init__(nodeName=nodeName, value=value, defaultValue=defaultValue)
        
        self.minValue = minValue
        self.maxValue = maxValue
        self.stepSize = stepSize

    
    def _convertValueType(self, value):
        """ Converts to int so that self.value always is of that type.
        """
        return int(value)
        
    
    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return "min = {}, max = {}, step = {}".format(self.minValue, self.maxValue, self.stepSize)
    
    
    def createEditor(self, _option):
        """ Creates a spinbox for editing. 
            :type option: QStyleOptionViewItem
        """
        spinBox = QtGui.QSpinBox()

        if self.minValue is None:
            spinBox.setMinimum(np.iinfo('i').min)
        else: 
            spinBox.setMinimum(self.minValue) 

        if self.maxValue is None:
            spinBox.setMaximum(np.iinfo('i').max)
        else: 
            spinBox.setMaximum(self.maxValue) 

        spinBox.setSingleStep(self.stepSize)
        return spinBox
        
        
    def setEditorValue(self, spinBox, value):
        """ Provides the spinBox editor widget with a value to manipulate.
        """
        spinBox.setValue(value)
        
        
    def getEditorValue(self, spinBox):
        """ Gets data from the spinbox editor widget.
            
            :type editor: QWidget
        """
        spinBox.interpretText()
        value = spinBox.value()
        return value

        