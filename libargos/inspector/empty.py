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
        

    def _updateRti(self):
        """ Draws the inspector widget when an RTI is updated.
        """
        logger.debug("EmptyInspector._drawContents: {}".format(self))
        
        slicedArray = self.collector.getSlicedArray()
        if slicedArray is None:
            text = "<None>"
        else:
            text = str(slicedArray.shape)
        
        logger.debug("_drawContents: {}".format(text))
        
        if DEBUGGING:
            self.label.setText(text)

