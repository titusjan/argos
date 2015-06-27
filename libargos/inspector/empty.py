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

""" Empty inspector.
"""
import logging

from libargos.info import DEBUGGING
from libargos.config.emptycti import EmptyCti
from libargos.inspector.abstract import AbstractInspector
from libargos.qt import QtGui

logger = logging.getLogger(__name__)


class EmptyInspector(AbstractInspector):
    """ Empty inspector, mainly for debugging purposes.
    
        Displays the shape of the selected array if Argos is in debugging mode, otherwise
        the widget is empty.
    """
    def __init__(self, collector, parent=None):
        
        super(EmptyInspector, self).__init__(collector, parent=parent)
        
        self.label = QtGui.QLabel()
        self.contentsLayout.addWidget(self.label)

        
    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple(['Y', 'X'])
          
            
    @classmethod        
    def createConfig(cls):
        """ Creates a config tree item (CTI) hierarchy containing default children.
        """
        rootItem = EmptyCti('inspector')
        
        if DEBUGGING:
            # Some test config items.
            from libargos.config.untypedcti import UntypedCti
            from libargos.config.stringcti import StringCti
            from libargos.config.intcti import IntCti
            from libargos.config.floatcti import FloatCti
            from libargos.config.boolcti import BoolCti
            from libargos.config.choicecti import ChoiceCti
            from libargos.config.qtctis import ColorCti
            
            grpItem = EmptyCti("group")
            rootItem.insertChild(grpItem)
            
            lcItem = UntypedCti('line color', defaultData=123)
            grpItem.insertChild(lcItem)
    
            grpItem.insertChild(IntCti('line-1 color', defaultData=-7, minValue = -5, stepSize=2))
            rootItem.insertChild(StringCti('letter', defaultData='aa', maxLength = 1))
            grpItem.insertChild(FloatCti('width', defaultData=0, minValue =5, 
                                         stepSize=0.45, decimals=3))
            rootItem.insertChild(BoolCti('grid', defaultData=True))
            rootItem.insertChild(ChoiceCti('hobbit', defaultData=2, 
                                           displayValues=['Frodo', 'Sam', 'Pippin', 'Merry']))
            rootItem.insertChild(ColorCti('favorite color', defaultData="#22FF33"))
                    
        return rootItem
        

    def _updateRti(self):
        """ Draws the inspector widget when an RTI is updated.
        """
        logger.debug("EmptyInspector._drawContents: {}".format(self))
        
        slicedArray = self.collector.getSlicedArray()
        if slicedArray is None:
            text = "<None>"
        else:
            text = str(slicedArray.shape)
        
        logger.debug("_updateRti shape: {}".format(text))
        
        if DEBUGGING:
            self.label.setText("slice shape: {}".format(text))
            
            
            
