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

""" PyQtGraph 1D line plot
"""
from __future__ import division, print_function

import logging
import pyqtgraph as pg
#from pyqtgraph.Qt import QtGui

from libargos.info import DEBUGGING
from libargos.inspector.abstract import AbstractInspector
from libargos.utils.cls import array_has_real_numbers

logger = logging.getLogger(__name__)


class PgLinePlot1d(AbstractInspector):
    """ Inspector that contains a PyQtGraph 1-dimensional line plot
    """
    
    def __init__(self, collector, parent=None):
        """ Constructor. See AbstractInspector constructor for parameters.
        """
        super(PgLinePlot1d, self).__init__(collector, parent=parent)
        
        self.plotWidget = pg.PlotWidget(name='main_plot') 
        self.contentsLayout.addWidget(self.plotWidget)
        
        self.plotDataItem = self.plotWidget.plot()
        self.plotDataItem.setPen((200,200,100)) # QPen
        
        
    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple(['Y'])
            

    def _drawContents(self):
        """ Draws the inspector widget when no input is available.
            The default implementation shows an error message. Descendants should override this.
        """
        slicedArray = self.collector.getSlicedArray()
        
        if slicedArray is None or not array_has_real_numbers(slicedArray):
            self.plotDataItem.clear()
            if not DEBUGGING:
                raise ValueError("No data available or it does not contain real numbers")
        else:
            self.plotDataItem.setData(slicedArray)
            
        