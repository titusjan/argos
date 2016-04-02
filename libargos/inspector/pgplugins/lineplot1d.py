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

logger = logging.getLogger(__name__)

USE_SIMPLE_PLOT = False

if USE_SIMPLE_PLOT:
    # An experimental simplification of PlotItem. Not included in the distribution
    logger.warn("Using SimplePlotItem as PlotItem")
    from pyqtgraph.graphicsItems.PlotItem.simpleplotitem import SimplePlotItem
else:
    from pyqtgraph.graphicsItems.PlotItem import PlotItem as SimplePlotItem


from libargos.qt import QtGui
from libargos.info import DEBUGGING
from libargos.config.groupcti import MainGroupCti, GroupCti
from libargos.config.boolcti import BoolGroupCti, BoolCti
from libargos.config.choicecti import ChoiceCti
from libargos.config.qtctis import PenCti, ColorCti, createPenStyleCti, createPenWidthCti
from libargos.config.floatcti import FloatCti
from libargos.config.intcti import IntCti
from libargos.inspector.abstract import AbstractInspector
from libargos.inspector.pgplugins.pgctis import PgPlotItemCti, PgAxisLabelCti, PgAxisAutoRangeCti
from libargos.utils.cls import array_has_real_numbers, check_class


class PgLinePlot1dCti(MainGroupCti):
    """ Configuration tree for a PgLinePlot1d inspector
    """
    def __init__(self, nodeName, pgLinePlot1d, defaultData=None):
        """ Constructor

            Maintains a link to the target pgLinePlot1d inspector, so that changes in the
            configuration can be applied to the target by simply calling the apply method.
            Vice versa, it can connect signals to the target.
        """
        super(PgLinePlot1dCti, self).__init__(nodeName, defaultData=defaultData)

        check_class(pgLinePlot1d, PgLinePlot1d)
        self.pgLinePlot1d = pgLinePlot1d
    
        self.insertChild(ChoiceCti('title', 0, editable=True, 
                                    configValues=["{path} {slices}", "{name} {slices}"]))
        self.insertChild(BoolCti("anti-alias", True))

        # Grid (not in ViewBox but a separate group so it can be toggled on/off with one checkbox)
        gridItem = self.insertChild(BoolGroupCti('grid', True, expanded=False))
        gridItem.insertChild(BoolCti('x-axis', True))
        gridItem.insertChild(BoolCti('y-axis', True))
        gridItem.insertChild(FloatCti('alpha', 0.20, 
                                      minValue=0.0, maxValue=1.0, stepSize=0.01, decimals=2))

        # Axes
        plotItem = self.pgLinePlot1d.plotItem
        self.plotItemCti = self.insertChild(PgPlotItemCti(plotItem))

        xAxisCti = self.plotItemCti.xAxisCti
        xAxisCti.insertChild(PgAxisLabelCti(plotItem, 'bottom', self.pgLinePlot1d.collector,
                configValues=["{x-dim}"]))

        yAxisCti = self.plotItemCti.yAxisCti
        yAxisCti.insertChild(PgAxisLabelCti(plotItem, 'left', self.pgLinePlot1d.collector,
                configValues=["{name} {unit}", "{path} {unit}", "{name}", "{path}", "{raw-unit}"]))

        # Pen
        penItem = self.insertChild(GroupCti('pen'))
        penItem.insertChild(ColorCti('color', QtGui.QColor('#FF0066')))
        lineItem = penItem.insertChild(BoolCti('line', True, expanded=False,
                                               childrenDisabledValue=False))
        lineItem.insertChild(createPenStyleCti('style'))
        lineItem.insertChild(createPenWidthCti('width'))
        defaultShadowPen = QtGui.QPen(QtGui.QColor('#BFBFBF'))
        defaultShadowPen.setWidth(0)
        lineItem.insertChild(PenCti("shadow", False, expanded=False,  
                                    resetTo=QtGui.QPen(defaultShadowPen), 
                                    includeNoneStyle=True, includeZeroWidth=True))

        symbolItem = penItem.insertChild(BoolCti("symbol", False, expanded=False,
                                         childrenDisabledValue=False))
        symbolItem.insertChild(ChoiceCti("shape", 0, 
           displayValues=['circle', 'square', 'triangle', 'diamond', 'plus'],  
           configValues=['o', 's', 't', 'd', '+']))
        symbolItem.insertChild(IntCti('size', 5, minValue=0, maxValue=100, stepSize=1))


    def initTarget(self):
        """ Applies the configuration to the target PgLinePlot1d it monitors.
        """
        self.plotItemCti.initTarget()


    def drawTarget(self):
        """ Applies the configuration to the target PgLinePlot1d it monitors.
        """
        self.plotItemCti.drawTarget()


class PgLinePlot1d(AbstractInspector):
    """ Inspector that contains a PyQtGraph 1-dimensional line plot
    """
    
    def __init__(self, collector, parent=None):
        """ Constructor. See AbstractInspector constructor for parameters.
        """
        super(PgLinePlot1d, self).__init__(collector, parent=parent)

        self.viewBox = pg.ViewBox(border=pg.mkPen("#000000", width=1))

        self.plotItem = SimplePlotItem(name='1d_line_plot_#{}'.format(self.windowNumber),
                                       enableMenu=False, viewBox=self.viewBox)
        self.viewBox.setParent(self.plotItem)

        self.graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self.titleLabel = self.graphicsLayoutWidget.addLabel('<plot title goes here>', 0, 0)
        self.graphicsLayoutWidget.addItem(self.plotItem, 1, 0)

        self.contentsLayout.addWidget(self.graphicsLayoutWidget)

        self._config = PgLinePlot1dCti('inspector', pgLinePlot1d=self) # TODO: should be able to change nodeName without --reset

        
    def finalize(self):
        """ Is called before destruction. Can be used to clean-up resources
        """
        logger.debug("Finalizing: {}".format(self))
        self.plotItem.close()
        self.graphicsLayoutWidget.close()

        
    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple(['X'])


    def _clearContents(self):
        """ Draws the inspector widget when no input is available.
        """
        self.plotItem.clear()
        self.titleLabel.setText('')
        self.config.initTarget()



    def _drawContents(self):
        """ Draws the RTI
        """
        slicedArray = self.collector.getSlicedArray()
        if slicedArray is None or not array_has_real_numbers(slicedArray):
            logger.debug("Clearing inspector: no data available or it does not contain real numbers")
            self._clearContents()
            return

        # Valid plot data here
        rtiInfo = self.collector.getRtiInfo()

        self.plotItem.clear() # TODO

        self.titleLabel.setText(self.configValue('title').format(**rtiInfo))

        self.plotItem.showGrid(x=self.configValue('grid/x-axis'),
                               y=self.configValue('grid/y-axis'),
                               alpha=self.configValue('grid/alpha'))
        self.plotItem.updateGrid()

        antiAlias = self.configValue('anti-alias')
        color = self.configValue('pen/color')

        if self.configValue('pen/line'):
            pen = QtGui.QPen()
            pen.setCosmetic(True)
            pen.setColor(color)
            pen.setWidthF(self.configValue('pen/line/width'))
            pen.setStyle(self.configValue('pen/line/style'))
            shadowCti = self.config.findByNodePath('pen/line/shadow')
            shadowPen = shadowCti.createPen(altStyle=pen.style(), altWidth=2.0 * pen.widthF())
        else:
            pen = None
            shadowPen = None

        drawSymbols = self.configValue('pen/symbol')
        symbolShape = self.configValue('pen/symbol/shape') if drawSymbols else None
        symbolSize  = self.configValue('pen/symbol/size') if drawSymbols else 0.0
        symbolPen   = pen if drawSymbols else None
        symbolBrush = QtGui.QBrush(color) if drawSymbols else None

        self.plotDataItem = self.plotItem.plot(pen=pen, shadowPen=shadowPen,
                                               symbol=symbolShape, symbolSize=symbolSize,
                                               symbolPen=symbolPen, symbolBrush=symbolBrush,
                                               antialias=antiAlias)



        self.plotDataItem.setData(slicedArray)

        self.config.drawTarget()



        