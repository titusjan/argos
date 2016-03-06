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

""" PyQtGraph 2D image plot
"""
from __future__ import division, print_function

import logging
import pyqtgraph as pg

logger = logging.getLogger(__name__)

USE_SIMPLE_PLOT = True
if USE_SIMPLE_PLOT:
    logger.warn("Using SimplePlotItem as PlotItem")
    from pyqtgraph.graphicsItems.PlotItem.simpleplotitem import SimplePlotItem as PlotItem
else:
    from pyqtgraph.graphicsItems.PlotItem import PlotItem


from libargos.info import DEBUGGING
from libargos.config.groupcti import MainGroupCti
from libargos.config.boolcti import BoolCti
from libargos.inspector.abstract import AbstractInspector
from libargos.utils.cls import array_has_real_numbers

logger = logging.getLogger(__name__)

# TODO: look in imageAnalysis.py PyQtGraph example to see how to enable axis labels and disable the menu
class PgImagePlot2d(AbstractInspector):
    """ Inspector that contains a PyQtGraph 2-dimensional image plot
    """
    
    def __init__(self, collector, parent=None):
        """ Constructor. See AbstractInspector constructor for parameters.
        """
        super(PgImagePlot2d, self).__init__(collector, parent=parent)
        
        self.viewBox = pg.ViewBox(border=pg.mkPen("#000000", width=1))#), lockAspect=1.0)
        self.plotItem = pg.PlotItem(name='1d_line_plot_#{}'.format(self.windowNumber),
                                    title='', enableMenu=True, viewBox=self.viewBox)  # TODO: enableMenu=False
        self.viewBox.setParent(self.plotItem)

        self.imageItem = pg.ImageItem()
        self.plotItem.addItem(self.imageItem)

        self.graphicsView = pg.GraphicsView()
        self.graphicsView.setCentralItem(self.plotItem)
        self.contentsLayout.addWidget(self.graphicsView)

        # Connect signals
        #self.viewBox.sigStateChanged.connect(self.config.viewBoxCti.viewBoxChanged)
        
        
    def finalize(self):
        """ Is called before destruction. Can be used to clean-up resources
        """
        # Disconnect signals
        #self.viewBox.sigStateChanged.disconnect(self.config.viewBoxCti.viewBoxChanged)
        self.plotItem.close()
        self.graphicsView.close()

        
    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple(['Rows', 'Columns'])
           

    @classmethod        
    def createConfig(cls):
        """ Creates a config tree item (CTI) hierarchy containing default children.
        """
        rootItem = MainGroupCti(nodeName='inspector')
        rootItem.insertChild(BoolCti('auto levels', defaultData=True))
        rootItem.insertChild(BoolCti('auto range', defaultData=True))
        rootItem.insertChild(BoolCti('lock aspect ratio', defaultData=False))

        return rootItem
    
                
    def _initContents(self):
        """ Draws the inspector widget when no input is available. 
        """
        #viewBox = self.imageView.view
        self.viewBox.setAspectLocked(self.configValue('lock aspect ratio'))


    def _updateRti(self):
        """ Draws the inspector widget when no input is available.
        """
        slicedArray = self.collector.getSlicedArray()
        
        if slicedArray is None or not array_has_real_numbers(slicedArray):
            self.imageItem.clear()
            if not DEBUGGING: # TODO: is this an error?
                raise ValueError("No data available or it does not contain real numbers")
        else:
            # TODO: cache config values?
            autoRange = self.configValue('auto range')
            autoLevels = self.configValue('auto levels')
            
            # Unfortunately, PyQtGraph uses the following dimension order: T, X, Y, Color.
            # We need to transpose the slicedArray ourselves because axes = {'x':1, 'y':0} 
            # doesn't seem to do anything.
            self.imageItem.setImage(slicedArray.transpose(),
                                    autoRange=autoRange, autoLevels=autoLevels)

        