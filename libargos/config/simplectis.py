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
from libargos.qt import QtGui, getQApplicationInstance, Qt


logger = logging.getLogger(__name__)

# Use setIndexWidget()?
        
# TODO: QCompleter? See demos/spreadsheet/spreadsheetdelegate.py
# TODO: FloatCti using QDoubleSpinBox
# TODO: Nullable bool with tri-state checkbox
# TODO: Bool and CombiBox  
# TODO: Date selector.
# TODO: Color selector. Font selector?
# TODO: reset button
# TODO: None takes value of parent


class StringCti(BaseCti):
    """ Config Tree Item to store a string. It can be edited with a QLineEdit.
        The string can have an optional maximum length.

    """
    def __init__(self, nodeName='', value=USE_DEFAULT_VALUE, defaultValue='', 
                 maxLength=None):
        """ Constructor. 
        
            :param maxLength: maximum length of the string
            
            For the other parameters see the BaseCti constructor documentation.
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
    
    
    def createEditor(self, delegate, parent, _option):
        """ Creates a QSpinBox for editing. 
            :type option: QStyleOptionViewItem        
        """
        editor = QtGui.QLineEdit(parent)
        if self.maxLength is not None:
            editor.setMaxLength(self.maxLength)
        return editor
        
        
    def setEditorValue(self, editor, value):
        """ Provides the editor widget with a value to manipulate.
        """
        lineEditor = editor
        lineEditor.setText(value)
        
        
    def getEditorValue(self, editor):
        """ Gets data from the editor widget.
        """
        lineEditor = editor
        return lineEditor.text()



class IntegerCti(BaseCti):
    """ Config Tree Item to store an integer. It can be edited using a QSinBox.
    """
    def __init__(self, nodeName='', value=USE_DEFAULT_VALUE, defaultValue=0, 
                 minValue = None, maxValue = None, stepSize = 1):
        """ Constructor
            
            :param minValue: minimum value allowed when editing (use None for no minimum)
            :param maxValue: maximum value allowed when editing (use None for no maximum)
            :param stepSize: steps between values when ediging (default = 1)
                    
            For the other parameters see the BaseCti constructor documentation.
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
    
    
    def createEditor(self, delegate, parent, _option):
        """ Creates a QSpinBox for editing. 
            :type option: QStyleOptionViewItem
        """
        spinBox = QtGui.QSpinBox(parent)

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
        """ Provides the spin box editor widget with a value to manipulate.
        """
        spinBox.setValue(value)
        
        
    def getEditorValue(self, spinBox):
        """ Gets data from the spin box editor widget.
        """
        spinBox.interpretText()
        value = spinBox.value()
        return value

        

class BoolCti(BaseCti):
    """ Config Tree Item to store an integer. It can be edited using a QSinBox.
    """
    def __init__(self, nodeName='', value=USE_DEFAULT_VALUE, defaultValue=False):
        """ Constructor

            For the parameters see the BaseCti constructor documentation.
        """
        super(BoolCti, self).__init__(nodeName=nodeName, value=value, defaultValue=defaultValue)

    
    def _convertValueType(self, value):
        """ Converts to bool so that self.value always is of that type.
        """
        return bool(value)
        

    def createEditor(self, delegate, parent, _option):
        """ Creates a QSpinBox for editing. 
            :type option: QStyleOptionViewItem        
        """
        checkBox = QtGui.QCheckBox(parent)
        checkBox.setFocusPolicy(Qt.StrongFocus) # See QAbstractItemDelegate.createEditor docs
        checkBox.clicked.connect(delegate.commitAndCloseEditor)
        return checkBox

        
    def setEditorValue(self, checkBox, value):
        """ Provides the check box editor widget with a value to manipulate.
        """
        checkBox.setChecked(value)
        
        
    def getEditorValue(self, checkBox):
        """ Gets data from the check box editor widget.
        """
        return checkBox.isChecked()

        
    def paintDisplayValue(self, painter, option, value):
        """ Paints a check box on the painter.
        """
        checkBox = QtGui.QStyleOptionButton()
        
        checkBox.state = QtGui.QStyle.State_Enabled
        checkBox.rect = option.rect
        
        if value:
            checkBox.state = QtGui.QStyle.State_On | QtGui.QStyle.State_Enabled
        else:
            checkBox.state = QtGui.QStyle.State_Off | QtGui.QStyle.State_Enabled

        qApp = getQApplicationInstance()
        qApp.style().drawControl(QtGui.QStyle.CE_CheckBox, checkBox, painter)
        return True
    
                