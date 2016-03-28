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

USE_SIMPLE_PLOT = False

if USE_SIMPLE_PLOT:
    logger.warn("Using SimplePlotItem as PlotItem")
    from pyqtgraph.graphicsItems.PlotItem.simpleplotitem import SimplePlotItem
else:
    from pyqtgraph.graphicsItems.PlotItem import PlotItem as SimplePlotItem

from libargos.info import DEBUGGING
from libargos.config.groupcti import MainGroupCti
from libargos.config.boolcti import BoolCti
from libargos.config.choicecti import ChoiceCti
from libargos.inspector.abstract import AbstractInspector
from libargos.inspector.pgplugins.pgctis import PgAxisCti, PgIndependendAxisCti, PgPlotItemCti
from libargos.utils.cls import array_has_real_numbers, check_class

logger = logging.getLogger(__name__)


class __not_used__PgImageAxisCti(PgAxisCti):
    """ Configuration tree item for a plot axis showing a dependend variable
    """
    def __init__(self, nodeName, defaultData=None, axisNumber=None, axisName=None):
        """ Constructor
        """
        super(PgImageAxisCti, self).__init__(nodeName, defaultData=defaultData,
                                             axisNumber=axisNumber)
        self.axisName = axisName
        self.insertChild(ChoiceCti('label', 0, editable=True,
                                    configValues=["{{{}-dim}}".format(axisName)]),
                         position=0)


class PgImagePlot2dCti(MainGroupCti):
    """ Configuration tree for a PgLinePlot1d inspector
    """
    def __init__(self, nodeName, pgImagePlot2d, defaultData=None):
        """ Constructor

            Maintains a link to the target pgImagePlot2d inspector, so that changes in the
            configuration can be applied to the target by simply calling the apply method.
            Vice versa, it can connect signals to the target.
        """
        super(PgImagePlot2dCti, self).__init__(nodeName, defaultData=defaultData)
        check_class(pgImagePlot2d, PgImagePlot2d)
        self.pgImagePlot2d = pgImagePlot2d

        self.insertChild(ChoiceCti('title', 0, editable=True,
                                   configValues=["{path} {slices}", "{name} {slices}"]))

        viewBox = pgImagePlot2d.plotItem.getViewBox()
        plotItemCti = PgPlotItemCti('axes', plotItem=pgImagePlot2d.plotItem,
                        xAxisCti=PgIndependendAxisCti('x-axis', viewBox, 0, axisName='x'),
                        yAxisCti=PgIndependendAxisCti('y-axis', viewBox, 1, axisName='y'))
        self.plotItemCti = self.insertChild(plotItemCti)

        self.insertChild(BoolCti('auto levels', True))


    def apply(self):
        """ Applies the configuration to the target PgLinePlot1d it monitors.
        """
        self.plotItemCti.apply()



class PgImagePlot2d(AbstractInspector):
    """ Inspector that contains a PyQtGraph 2-dimensional image plot
    """
    
    def __init__(self, collector, parent=None):
        """ Constructor. See AbstractInspector constructor for parameters.
        """
        super(PgImagePlot2d, self).__init__(collector, parent=parent)

        self.viewBox = pg.ViewBox(border=pg.mkPen("#000000", width=1))
        self.plotItem = SimplePlotItem(name='1d_line_plot_#{}'.format(self.windowNumber),
                                       enableMenu=False, viewBox=self.viewBox)
        self.viewBox.setParent(self.plotItem)

        self.imageItem = pg.ImageItem()
        self.plotItem.addItem(self.imageItem)

        self.histLutItem = pg.HistogramLUTItem()
        self.histLutItem.setImageItem(self.imageItem)

        self.graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self.titleLabel = self.graphicsLayoutWidget.addLabel('My label', 0, 0, colspan=2)
        self.graphicsLayoutWidget.addItem(self.plotItem, 1, 0)
        self.graphicsLayoutWidget.addItem(self.histLutItem, 1, 1)

        self.contentsLayout.addWidget(self.graphicsLayoutWidget)

        self._config = PgImagePlot2dCti('inspector', pgImagePlot2d=self)

        
    def finalize(self):
        """ Is called before destruction. Can be used to clean-up resources.
        """
        logger.debug("Finalizing: {}".format(self))
        self.plotItem.close()
        self.graphicsLayoutWidget.close()

        
    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple(['Y', 'X'])

                
    def _initContents(self):
        """ Draws the inspector widget when no input is available. 
        """
        self.viewBox.invertY(False) # TODO
        self.imageItem.clear()
        self.titleLabel.setText('')
        self.plotItem.setLabel('left', '')
        self.plotItem.setLabel('bottom', '')


    def _drawContents(self):
        """ Draws the inspector widget when no input is available.
        """
        slicedArray = self.collector.getSlicedArray()
        
        if slicedArray is None or not array_has_real_numbers(slicedArray):
            self._initContents()
            if DEBUGGING:
                return
            else: # TODO: this is not an error
                raise ValueError("No data available or it does not contain real numbers")

        # Valid plot data here

        rtiInfo = self.collector.getRtiInfo()
        self.titleLabel.setText(self.configValue('title').format(**rtiInfo))
        self.plotItem.setLabel('left',   self.configValue('axes/y-axis/label').format(**rtiInfo)) # TODO: to ViewBox?
        self.plotItem.setLabel('bottom', self.configValue('axes/x-axis/label').format(**rtiInfo))

        # Unfortunately, PyQtGraph uses the following dimension order: T, X, Y, Color.
        # We need to transpose the slicedArray ourselves because axes = {'x':1, 'y':0}
        # doesn't seem to do anything.
        self.imageItem.setImage(slicedArray.transpose(),
                                autoLevels = self.configValue('auto levels'))

        self.histLutItem.setLevels(slicedArray.min(), slicedArray.max())

        self.config.apply()
