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
import numpy as np
import pyqtgraph as pg

from libargos.info import DEBUGGING
from libargos.config.boolcti import BoolCti
from libargos.config.choicecti import ChoiceCti
from libargos.config.groupcti import MainGroupCti
from libargos.inspector.abstract import AbstractInspector, InvalidDataError
from libargos.inspector.pgplugins.pgctis import (X_AXIS, Y_AXIS, BOTH_AXES,
                                                 defaultAutoRangeMethods,
                                                 PgMainPlotItemCti, PgAxisLabelCti,
                                                 PgAxisFlipCti, PgAspectRatioCti,
                                                 PgAxisRangeCti, PgHistLutColorRangeCti,
                                                 PgGradientEditorItemCti)
from libargos.inspector.pgplugins.pgplotitem import ArgosPgPlotItem
from libargos.utils.cls import array_has_real_numbers, check_class

logger = logging.getLogger(__name__)


class PgImagePlot2dCti(PgMainPlotItemCti):
    """ Configuration tree for a PgLinePlot1d inspector
    """
    def __init__(self, pgImagePlot2d, nodeName):
        """ Constructor

            Maintains a link to the target pgImagePlot2d inspector, so that changes in the
            configuration can be applied to the target by simply calling the apply method.
            Vice versa, it can connect signals to the target.
        """
        super(PgImagePlot2dCti, self).__init__(pgImagePlot2d.plotItem, nodeName)
        check_class(pgImagePlot2d, PgImagePlot2d)
        self.pgImagePlot2d = pgImagePlot2d
        plotItem = self.pgImagePlot2d.plotItem
        viewBox = plotItem.getViewBox()

        self.insertChild(ChoiceCti('title', 0, editable=True,
                                   configValues=["{path} {slices}", "{name} {slices}"]),
                         position=-2) # before the xAxisCti and yAxisCti

        #### Axes ####
        self.aspectLockedCti = self.insertChild(PgAspectRatioCti(viewBox), position=-2)

        xAxisCti = self.xAxisCti
        #xAxisCti.insertChild(PgAxisShowCti(plotItem, 'bottom')) # disabled, seems broken
        xAxisCti.insertChild(PgAxisLabelCti(plotItem, 'bottom', self.pgImagePlot2d.collector,
            defaultData=1, configValues=[PgAxisLabelCti.NO_LABEL, "{x-dim}"]))
        xAxisCti.insertChild(PgAxisFlipCti(viewBox, X_AXIS))
        xAxisCti.insertChild(PgAxisRangeCti(viewBox, X_AXIS))

        yAxisCti = self.yAxisCti
        #yAxisCti.insertChild(PgAxisShowCti(plotItem, 'left'))  # disabled, seems broken
        yAxisCti.insertChild(PgAxisLabelCti(plotItem, 'left', self.pgImagePlot2d.collector,
            defaultData=1, configValues=[PgAxisLabelCti.NO_LABEL, "{y-dim}"]))
        yAxisCti.insertChild(PgAxisFlipCti(viewBox, Y_AXIS))
        yAxisCti.insertChild(PgAxisRangeCti(viewBox, Y_AXIS))

        #### Color scale ####
        self.insertChild(PgGradientEditorItemCti(self.pgImagePlot2d.histLutItem.gradient))
        rangeFunctions = defaultAutoRangeMethods(self.pgImagePlot2d)
        self.insertChild(PgHistLutColorRangeCti(pgImagePlot2d.histLutItem, rangeFunctions,
                                                nodeName="color range"))

        histViewBox = pgImagePlot2d.histLutItem.vb
        histViewBox.enableAutoRange(Y_AXIS, False)
        self.histRangeCti = self.insertChild(PgAxisRangeCti(histViewBox, Y_AXIS,
                                                            nodeName='histogram range'))



class PgImagePlot2d(AbstractInspector):
    """ Inspector that contains a PyQtGraph 2-dimensional image plot
    """
    
    def __init__(self, collector, parent=None):
        """ Constructor. See AbstractInspector constructor for parameters.
        """
        super(PgImagePlot2d, self).__init__(collector, parent=parent)

        # The sliced array is kept in memory. This may be different per inspector, e.g. 3D
        # inspectors may decide that this uses to much memory. The slice is therefor not stored
        # in the collector.
        self.slicedArray = None

        self.viewBox = pg.ViewBox(border=pg.mkPen("#000000", width=1))
        self.plotItem = ArgosPgPlotItem(name='2d_image_plot_#{}'.format(self.windowNumber),
                                        enableMenu=False, viewBox=self.viewBox)
        self.viewBox.setParent(self.plotItem)
        self.viewBox.disableAutoRange(BOTH_AXES)

        self.imageItem = pg.ImageItem()
        self.plotItem.addItem(self.imageItem)

        self.histLutItem = pg.HistogramLUTItem() # what about GradientLegend?
        self.histLutItem.setImageItem(self.imageItem)
        self.histLutItem.vb.setMenuEnabled(False)

        self.graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self.titleLabel = self.graphicsLayoutWidget.addLabel('<Title label>', 0, 0, colspan=2)
        self.graphicsLayoutWidget.addItem(self.plotItem, 1, 0)
        self.graphicsLayoutWidget.addItem(self.histLutItem, 1, 1)

        self.contentsLayout.addWidget(self.graphicsLayoutWidget)

        self._config = PgImagePlot2dCti(pgImagePlot2d=self, nodeName='inspector')

        
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

                
    def _clearContents(self):
        """ Draws the inspector widget when no input is available. 
        """
        logger.debug("Clearing inspector contents")
        #self.imageItem.clear() # Don't use clear as it alters the (auto)range.
        self.imageItem.setImage(None) # TODO: this also alters the auto(range). Use clear again?
        self.titleLabel.setText('')


    def _drawContents(self):
        """ Draws the inspector widget when no input is available.
        """
        self.slicedArray = self.collector.getSlicedArray()
        if self.slicedArray is None or not array_has_real_numbers(self.slicedArray):
            self._clearContents()
            raise InvalidDataError("No data available or it does not contain real numbers")

        #self.imageItem.clear() # Don't use clear as it resets the autoscale enabled?

        # Valid plot data here

        rtiInfo = self.collector.getRtiInfo()
        self.titleLabel.setText(self.configValue('title').format(**rtiInfo))

        # PyQtGraph uses the following dimension order: T, X, Y, Color.
        # We need to transpose the slicedArray ourselves because axes = {'x':1, 'y':0}
        # doesn't seem to do anything.
        self.imageItem.setImage(self.slicedArray.transpose(), autoLevels=False)

        self.config.updateTarget()

