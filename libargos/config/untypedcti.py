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

""" Contains the UntypedCti and UntypedCtiEditor classes 
"""
import logging

from libargos.config.abstractcti import AbstractCti, AbstractCtiEditor
from libargos.qt import QtGui
from libargos.utils.misc import NOT_SPECIFIED

logger = logging.getLogger(__name__)


    
class UntypedCti(AbstractCti):
    """ Config Tree Item to store a any type of data as long as it can be edited with a QLineEdit.
    
        Typically it's better to use 'typed' CTIs, where the data is always internally stored in
        the same type (enforcec by _enforceDataType). This class is currently only used in the
        invisible root item of the ConfigTreeModel, and may become obsolete in the future.
    """
    def __init__(self, nodeName, data=NOT_SPECIFIED, defaultData=''):
        """ Constructor. For the parameters see the AbstractCti constructor documentation.
        """
        super(UntypedCti, self).__init__(nodeName, data=data, defaultData=defaultData)
    
    def _enforceDataType(self, value):
        """ Since UntypedCti can store any type of data no conversion will be done. 
        """
        return value
    
    def createEditor(self, delegate, parent, option):
        """ Creates an UntypedCtiEditor. 
            For the parameters see the AbstractCti constructor documentation.
        """
        return UntypedCtiEditor(self, delegate, parent=parent) 
    
        
        
class UntypedCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a QLineEdit for editing UntypedCti objects. 
    """
    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters 
        """
        super(UntypedCtiEditor, self).__init__(cti, delegate, parent=parent)
        self.lineEditor = self.addSubEditor(QtGui.QLineEdit(), isFocusProxy=True)
    
    def setData(self, value):
        """ Provides the main editor widget with a data to manipulate.
        """
        self.lineEditor.setText(str(value))
        
    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.lineEditor.text()
    
        
