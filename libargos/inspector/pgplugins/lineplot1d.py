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

from libargos.qt import QtGui
from libargos.info import DEBUGGING
from libargos.config.groupcti import MainGroupCti, GroupCti
from libargos.config.boolcti import BoolGroupCti, BoolCti
from libargos.config.choicecti import ChoiceCti
from libargos.config.qtctis import PenCti, ColorCti, createPenStyleCti, createPenWidthCti
from libargos.config.floatcti import FloatCti
from libargos.config.intcti import IntCti
from libargos.config.untypedcti import UntypedCti
from libargos.inspector.abstract import AbstractInspector
from libargos.utils.cls import array_has_real_numbers

logger = logging.getLogger(__name__)

                

class ViewBoxCti(GroupCti):
    """ Read-only config tree for inspecting a PyQtGraph ViewBox
    """
    def __init__(self, nodeName):
        
        # TODO: should configs have a link back to an inspector?
        super(ViewBoxCti, self).__init__(nodeName, defaultData=None)
        
        self.insertChild(UntypedCti("targetRange", [[0,1], [0,1]], 
            doc="Child coord. range visible [[xmin, xmax], [ymin, ymax]]"))

        self.insertChild(UntypedCti("viewRange", [[0,1], [0,1]], 
            doc="Actual range viewed"))

        self.insertChild(UntypedCti("xInverted", None))
        self.insertChild(UntypedCti("yInverted", None))
        self.insertChild(UntypedCti("aspectLocked", False, 
            doc="False if aspect is unlocked, otherwise float specifies the locked ratio."))
        self.insertChild(UntypedCti("autoRange", [True, True], 
            doc="False if auto range is disabled, otherwise float gives the fraction of data that is visible"))
        self.insertChild(UntypedCti("autoPan", [False, False], 
            doc="Whether to only pan (do not change scaling) when auto-range is enabled"))
        self.insertChild(UntypedCti("autoVisibleOnly", [False, False], 
            doc="Whether to auto-range only to the visible portion of a plot"))
        self.insertChild(UntypedCti("linkedViews", [None, None], 
            doc="may be None, 'viewName', or weakref.ref(view) a name string indicates that the view *should* link to another, but no view with that name exists yet."))
        self.insertChild(UntypedCti("mouseEnabled", [None, None]))
        self.insertChild(UntypedCti("mouseMode", None))
        self.insertChild(UntypedCti("enableMenu", None))
        self.insertChild(UntypedCti("wheelScaleFactor", None))
        self.insertChild(UntypedCti("background", None))
        
        self.limitsItem = self.insertChild(GroupCti("limits"))
        self.limitsItem.insertChild(UntypedCti("xLimits", [None, None], 
            doc="Maximum and minimum visible X values "))
        self.limitsItem.insertChild(UntypedCti("yLimits", [None, None], 
            doc="Maximum and minimum visible Y values"))
        self.limitsItem.insertChild(UntypedCti("xRange", [None, None], 
            doc="Maximum and minimum X range"))
        self.limitsItem.insertChild(UntypedCti("yRange", [None, None], 
            doc="Maximum and minimum Y range"))
                         

    def updateFromViewBox(self, viewBox):
        
        self.viewBox = viewBox
        for key, value in viewBox.state.items():
            if key != "limits":
                childItem = self.childByNodeName(key)
                childItem.data = value
            else:
                # limits contains a dictionary as well
                for limitKey, limitValue in value.items():
                    limitChildItem = self.limitsItem.childByNodeName(limitKey)
                    limitChildItem.data = limitValue


class PgAxisCti(GroupCti):
    """ Configuration tree for a plot axis
    """
    def __init__(self, nodeName, defaultData=None, axisNumber=None):
        """ Constructor
            :param axisIdx: 'x' or 'y'
        """
        super(PgAxisCti, self).__init__(nodeName, defaultData=defaultData)
        
        assert axisNumber in (0, 1), "axisName must be 0 or 1"
        self._axisNumber = axisNumber
        
        #self.insertChild(BoolCti("show", True)) # TODO:
        self.insertChild(BoolCti('logarithmic', False))
        
        # Keep a reference because this needs to be changed often/fast
        self.rangeItem = self.insertChild(GroupCti('range'))
        self.rangeMinItem = self.rangeItem.insertChild(FloatCti('min', 0.0))
        self.rangeMaxItem = self.rangeItem.insertChild(FloatCti('max', 0.0))
        
        self.autoRangeItem = self.rangeItem.insertChild(BoolCti("auto-range", True))
         
    
    def rangeChanged(self, viewBox, newRange):
        """ Called when the range of the axis is changed. Updates the range in the config tree.
        """
        self.rangeMinItem.data, self.rangeMaxItem.data = newRange
        self.autoRangeItem.data = bool(viewBox.autoRangeEnabled()[self._axisNumber])
        self.model.emitDataChanged(self.rangeItem)
        
        
    def getRange(self):
        return (self.rangeMinItem.data, self.rangeMaxItem.data) 
        
        
                

class PgLinePlot1dCti(MainGroupCti):
    """ Configuration tree for a PgLinePlot1d inspector
    """
    def __init__(self, nodeName, defaultData=None):
        
        super(PgLinePlot1dCti, self).__init__(nodeName, defaultData=defaultData)
    
        self.insertChild(ChoiceCti('title', 0, editable=True, 
                                    configValues=["{path} {slices}", "{name} {slices}"]))
        self.insertChild(BoolCti("anti-alias", False))

        # Grid
        gridItem = self.insertChild(BoolGroupCti('grid', True, expanded=False))
        gridItem.insertChild(BoolCti('X-axis', True))
        gridItem.insertChild(BoolCti('Y-axis', True))
        gridItem.insertChild(FloatCti('alpha', 0.20, 
                                      minValue=0.0, maxValue=1.0, stepSize=0.01, decimals=2))
    
        # Axes (keeping references to the axis CTIs because they need to be updated quickly when
        # the range changes; self.configValue may be slow.)
        #self.insertChild(BoolCti("aspect locked", False)) # TODO: implement?
        self.xAxisItem = self.insertChild(PgAxisCti('X-axis', axisNumber=0))
        self.yAxisItem = self.insertChild(PgAxisCti('Y-axis', axisNumber=1))
                
        # Pen
        penItem = self.insertChild(GroupCti('pen'))
        penItem.insertChild(ColorCti('color', QtGui.QColor('#1C8857')))
        lineItem = penItem.insertChild(BoolCti('line', True, expanded=False))
        lineItem.insertChild(createPenStyleCti('style'))
        lineItem.insertChild(createPenWidthCti('width'))
        defaultShadowPen = QtGui.QPen(QtGui.QColor('#BFBFBF'))
        defaultShadowPen.setWidth(0)
        lineItem.insertChild(PenCti("shadow", False, expanded=False,  
                                    resetTo=QtGui.QPen(defaultShadowPen), 
                                    includeNoneStyle=True, includeZeroWidth=True))

        symbolItem = penItem.insertChild(BoolCti("symbol", False, expanded=False)) 
        symbolItem.insertChild(ChoiceCti("shape", 0, 
           displayValues=['circle', 'square', 'triangle', 'diamond', 'plus'],  
           configValues=['o', 's', 't', 'd', '+']))
        symbolItem.insertChild(IntCti('size', 5, minValue=0, maxValue=100, stepSize=1))
        
        if DEBUGGING:
            self.viewBoxItem = self.insertChild(ViewBoxCti('viewbox'))
        else:
            self.viewBoxItem = None

        
                

class PgLinePlot1d(AbstractInspector):
    """ Inspector that contains a PyQtGraph 1-dimensional line plot
    """
    
    def __init__(self, collector, parent=None):
        """ Constructor. See AbstractInspector constructor for parameters.
        """
        super(PgLinePlot1d, self).__init__(collector, parent=parent)
        
        self._updatingPlot = False
        self.viewBox = pg.ViewBox(border=pg.mkPen("#000000", width=1))#), lockAspect=1.0)
        self.plotWidget = pg.PlotWidget(name='1d_line_plot_#{}'.format(self.windowNumber),
                                        title='', enableMenu=True, viewBox=self.viewBox) # TODO: enableMenu=False
        self.viewBox.setParent(self.plotWidget) 
        self.contentsLayout.addWidget(self.plotWidget)

        # Connect signals
        #plotItem.sigRangeChanged.connect(self.rangeChanged)
        #plotItem.sigXRangeChanged.connect(self.config.xAxisItem.rangeChanged)
        #plotItem.sigYRangeChanged.connect(self.config.yAxisItem.rangeChanged)
    
        self.viewBox.sigStateChanged.connect(self.viewBoxChanged)
        
        
    def finalize(self):
        """ Is called before destruction. Can be used to clean-up resources
        """
        logger.debug("Finalizing: {}".format(self))
        
        # Disconnect signals
        self.viewBox.sigStateChanged.disconnect(self.viewBoxChanged)                
        self.plotWidget.close()
                
        
    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple(['X-axis'])


    @classmethod        
    def createConfig(cls):
        """ Creates a config tree item (CTI) hierarchy containing default children.
        """
        return PgLinePlot1dCti('inspector') # TODO: should be able to change nodeName without --reset
        
                
    def _initContents(self):
        """ Draws the inspector widget when no input is available.
            Creates an empty plot.
        """
        self.plotWidget.clear()
        #self.plotWidget.showAxis('right')
        self.plotWidget.setLogMode(x=self.configValue('X-axis/logarithmic'), 
                                   y=self.configValue('Y-axis/logarithmic'))

        self.plotWidget.showGrid(x=self.configValue('grid/X-axis'), 
                                 y=self.configValue('grid/Y-axis'), 
                                 alpha=self.configValue('grid/alpha'))

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

        self.plotDataItem = self.plotWidget.plot(pen=pen, shadowPen=shadowPen, 
                                                 symbol=symbolShape, symbolSize=symbolSize,
                                                 symbolPen=symbolPen, symbolBrush=symbolBrush,
                                                 antialias=antiAlias)

    def _updateRti(self):
        """ Draws the RTI
        """
        slicedArray = self.collector.getSlicedArray()
        if slicedArray is None or not array_has_real_numbers(slicedArray):
            self.plotDataItem.clear()
            self.plotWidget.setTitle('')
            self.plotWidget.setLabel('left', '')
            self.plotWidget.setLabel('bottom', '')
            # TODO: is this an error
            if not DEBUGGING:
                raise ValueError("No data available or it does not contain real numbers.")
        
        else:        
            # Set (auto) range.
            # Block signals of the viewBox to prevent viewBoxChanged from being called.
            self._updatingPlot = True
            try:
                title = self.configValue('title').format(**self.collector.getRtiInfo())
                self.plotWidget.setTitle(title)
        
                ylabel = self.collector.dependentDimensionName()
                depUnit = self.collector.dependentDimensionUnit()
                if depUnit:
                    ylabel += ' ({})'.format(depUnit)
                self.plotWidget.setLabel('left', ylabel)
        
                xlabel = self.collector.independentDimensionNames()[0]
                indepUnit = self.collector.independentDimensionUnits()[0]
                if indepUnit:
                    xlabel += ' ({})'.format(indepUnit)
                self.plotWidget.setLabel('bottom', xlabel)
            
                self.plotDataItem.setData(slicedArray)
            
                autoRangeX = self.config.xAxisItem.autoRangeItem.data
                if autoRangeX:
                    logger.debug("enableAutoRange: {}, {}".format(self.viewBox.XAxis, autoRangeX))             
                    self.viewBox.enableAutoRange(self.viewBox.XAxis, autoRangeX)
                else:
                    logger.debug("Setting xRange: {}".format(self.config.xAxisItem.getRange()))
                    self.plotWidget.setRange(xRange = self.config.xAxisItem.getRange(),  
                                             padding=0, update=False, disableAutoRange=True)
                    
                autoRangeY = self.config.yAxisItem.autoRangeItem.data
                if autoRangeY:
                    logger.debug("enableAutoRange: {}, {}".format(self.viewBox.YAxis, autoRangeY))             
                    self.viewBox.enableAutoRange(self.viewBox.YAxis, autoRangeY)
                else:
                    logger.debug("Setting yRange: {}".format(self.config.yAxisItem.getRange()))
                    self.plotWidget.setRange(yRange = self.config.yAxisItem.getRange(), 
                                             padding=0, update=False, disableAutoRange=True)  

            finally:
                self._updatingPlot = False

    
    def rangeChanged(self, viewBox, ranges):
        """ Called when the range of one of the axis is changed. 
            Updates the axes ranges in the config tree.
        """
        xRange, yRange = ranges
        self.config.xAxisItem.rangeChanged(self.viewBox, xRange)
        self.config.yAxisItem.rangeChanged(self.viewBox, yRange)
            
            
    def viewBoxChanged(self, viewBox):
        """ Called when the x-range of the plot is changed. Updates the values in the config tree.
        """
        if self._updatingPlot:
            logger.debug("viewBoxChanged: ignored")
            return
        
        logger.debug("viewBoxChanged: {}".format(viewBox.autoRangeEnabled()))
        
        state = viewBox.state
        cfg = self.config
        xAxisEnabled, yAxisEnabled = viewBox.autoRangeEnabled()         

        cfg.xAxisItem.rangeMinItem.data, cfg.xAxisItem.rangeMaxItem.data = state['viewRange'][0]
        cfg.xAxisItem.autoRangeItem.data = bool(xAxisEnabled)
        
        cfg.yAxisItem.rangeMinItem.data, cfg.yAxisItem.rangeMaxItem.data = state['viewRange'][1]
        cfg.yAxisItem.autoRangeItem.data = bool(yAxisEnabled)
        
        if cfg.viewBoxItem:
            cfg.viewBoxItem.updateFromViewBox(viewBox)
        
        cfg.model.emitDataChanged(cfg)            
                    
        
        