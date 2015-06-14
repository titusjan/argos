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
from libargos.config.emptycti import EmptyCti
from libargos.config.colorcti import ColorCti
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
        
        self.plotWidget = pg.PlotWidget(name='1d_line_plot_#{}'.format(self.windowNumber),
                                        title='',  enableMenu=False) 
        self.contentsLayout.addWidget(self.plotWidget)
        
        
    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple(['Y'])


    @classmethod        
    def createConfig(cls):
        """ Creates a config tree item (CTI) hierarchy containing default children.
        """
        rootItem = EmptyCti(nodeName='inspector')
        rootItem.insertChild(ColorCti(nodeName='pen color', defaultData="#FF0000"))
        return rootItem
    
                
    def _initContents(self):
        """ Draws the inspector widget when no input is available.
            The default implementation shows an error message. Descendants should override this.
        """
        self.plotWidget.clear()
        self.plotWidget.setLabel('left', text='Hello <i>there</i>')
        #self.plotWidget.setLabel('right', text='')
        #self.plotWidget.setClipToView(True)
        self.plotWidget.showAxis('right')
        self.plotWidget.setLogMode(y=True)
        
        self.plotDataItem = self.plotWidget.plot()
        
        penColor = self.config.findByNodePath('pen color').data
        logger.debug("Pen color: {}".format(penColor))
        self.plotDataItem.setPen(penColor)
        #self.plotDataItem.setPen((200,200,100)) # QPen (yellow)
        #self.plotDataItem.setPen((0,0,200)) # QPen (yellow)
        


    def _updateRti(self):
        """ Draws the RTI
        """
        slicedArray = self.collector.getSlicedArray()
        
        if slicedArray is None or not array_has_real_numbers(slicedArray):
            self.plotDataItem.clear()
            if not DEBUGGING:
                raise ValueError("No data available or it does not contain real numbers")
        else:
            self.plotDataItem.setData(slicedArray)
            
        