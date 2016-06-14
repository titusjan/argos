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

ROW_TITLE,    COL_TITLE    = 0, 0  # colspan = 3
ROW_COLOR,    COL_COLOR    = 1, 0  # rowspan = 2
ROW_HOR_LINE, COL_HOR_LINE = 1, 1
ROW_IMAGE,    COL_IMAGE    = 2, 1
ROW_VER_LINE, COL_VER_LINE = 2, 2
ROW_PROBE,    COL_PROBE    = 3, 0  # colspan = 2


class PgImagePlot2dCti(PgMainPlotItemCti):
    """ Configuration tree for a PgLinePlot1d inspector
    """
    def __init__(self, pgImagePlot2d, nodeName):
        """ Constructor

            Maintains a link to the target pgImagePlot2d inspector, so that changes in the
            configuration can be applied to the target by simply calling the apply method.
            Vice versa, it can connect signals to the target.
        """
        super(PgImagePlot2dCti, self).__init__(pgImagePlot2d.imagePlotItem, nodeName)
        check_class(pgImagePlot2d, PgImagePlot2d)
        self.pgImagePlot2d = pgImagePlot2d
        imagePlotItem = self.pgImagePlot2d.imagePlotItem
        viewBox = imagePlotItem.getViewBox()

        self.insertChild(ChoiceCti('title', 0, editable=True,
                                   configValues=["{path} {slices}", "{name} {slices}"]),
                         position=-2) # before the xAxisCti and yAxisCti

        #### Axes ####
        self.aspectLockedCti = self.insertChild(PgAspectRatioCti(viewBox), position=-2)

        xAxisCti = self.xAxisCti
        #xAxisCti.insertChild(PgAxisShowCti(imagePlotItem, 'bottom')) # disabled, seems broken
        xAxisCti.insertChild(PgAxisLabelCti(imagePlotItem, 'bottom', self.pgImagePlot2d.collector,
            defaultData=1, configValues=[PgAxisLabelCti.NO_LABEL, "{x-dim}"]))
        self.xFlippedCti = xAxisCti.insertChild(PgAxisFlipCti(viewBox, X_AXIS))
        xAxisCti.insertChild(PgAxisRangeCti(viewBox, X_AXIS))

        yAxisCti = self.yAxisCti
        #yAxisCti.insertChild(PgAxisShowCti(imagePlotItem, 'left'))  # disabled, seems broken
        yAxisCti.insertChild(PgAxisLabelCti(imagePlotItem, 'left', self.pgImagePlot2d.collector,
            defaultData=1, configValues=[PgAxisLabelCti.NO_LABEL, "{y-dim}"]))
        self.yFlippedCti = yAxisCti.insertChild(PgAxisFlipCti(viewBox, Y_AXIS))
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

        self.probeCti = self.insertChild(BoolCti('show probe', True))
        self.horCrossPlotCti = self.insertChild(BoolCti('horizontal x-plot', True))
        self.verCrossPlotCti = self.insertChild(BoolCti('vertical x-plot', True))


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

        self.titleLabel = pg.LabelItem('title goes here...')

        # The image item
        self.imagePlotItem = ArgosPgPlotItem()
        self.viewBox = self.imagePlotItem.getViewBox()
        self.viewBox.disableAutoRange(BOTH_AXES)

        self.imageItem = pg.ImageItem()
        self.imagePlotItem.addItem(self.imageItem)

        self.histLutItem = pg.HistogramLUTItem() # what about GradientLegend?
        self.histLutItem.setImageItem(self.imageItem)
        self.histLutItem.vb.setMenuEnabled(False)

        # Cross hair plots and probe
        self.horCrossPlotItem = ArgosPgPlotItem()
        self.verCrossPlotItem = ArgosPgPlotItem()
        self.horPlotDataItem = self.horCrossPlotItem.plot()
        self.verPlotDataItem = self.verCrossPlotItem.plot()
        self.horCrossPlotItem.setXLink(self.imagePlotItem)
        self.verCrossPlotItem.setYLink(self.imagePlotItem)
        self.horCrossPlotItem.setLabel('left', ' ')
        self.verCrossPlotItem.setLabel('bottom', ' ')
        self.horCrossPlotItem.showAxis('top', True)
        self.horCrossPlotItem.showAxis('bottom', False)
        self.verCrossPlotItem.showAxis('right', True)
        self.verCrossPlotItem.showAxis('left', False)

        probePen = pg.mkPen("#BFBFBF")
        self.crossLineHorizontal = pg.InfiniteLine(angle=0, movable=False, pen=probePen)
        self.crossLineVertical = pg.InfiniteLine(angle=90, movable=False, pen=probePen)
        self.probeLabel = pg.LabelItem('', justify='left')

        # Layout

        # Hidding the horCrossPlotItem and horCrossPlotItem will still leave some space in the
        # grid layout. We therefore remove them from the layout instead. We need to know if they
        # are already added.
        self.horPlotAdded = False
        self.verPlotAdded = False

        self.graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self.contentsLayout.addWidget(self.graphicsLayoutWidget)

        self.graphicsLayoutWidget.addItem(self.titleLabel, ROW_TITLE, COL_TITLE, colspan=3)
        self.graphicsLayoutWidget.addItem(self.histLutItem, ROW_COLOR, COL_COLOR, rowspan=2)
        self.graphicsLayoutWidget.addItem(self.imagePlotItem, ROW_IMAGE, COL_IMAGE)
        self.graphicsLayoutWidget.addItem(self.probeLabel, ROW_PROBE, COL_PROBE, colspan=3)

        gridLayout = self.graphicsLayoutWidget.ci.layout # A QGraphicsGridLayout
        gridLayout.setHorizontalSpacing(10)
        gridLayout.setVerticalSpacing(10)
        #gridLayout.setRowSpacing(ROW_PROBE, 40)

        gridLayout.setRowStretchFactor(ROW_HOR_LINE, 1)
        gridLayout.setRowStretchFactor(ROW_IMAGE, 2)
        gridLayout.setColumnStretchFactor(COL_IMAGE, 2)
        gridLayout.setColumnStretchFactor(COL_VER_LINE, 1)

        # Configuration tree
        self._config = PgImagePlot2dCti(pgImagePlot2d=self, nodeName='inspector')

        # Connect signals
        # Based mouseMoved on crosshair.py from the PyQtGraph examples directory.
        # I did not use the SignalProxy because I did not see any difference.
        self.imagePlotItem.scene().sigMouseMoved.connect(self.mouseMoved)

        
    def finalize(self):
        """ Is called before destruction. Can be used to clean-up resources.
        """
        logger.debug("Finalizing: {}".format(self))
        self.imagePlotItem.scene().sigMouseMoved.connect(self.mouseMoved)
        self.imagePlotItem.close()
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

        gridLayout = self.graphicsLayoutWidget.ci.layout # A QGraphicsGridLayout

        if self.config.horCrossPlotCti.configValue:
            gridLayout.setRowStretchFactor(ROW_HOR_LINE, 1)
            if not self.horPlotAdded:
                self.graphicsLayoutWidget.addItem(self.horCrossPlotItem, ROW_HOR_LINE, COL_HOR_LINE)
                self.horPlotAdded = True
                gridLayout.activate()
        else:
            gridLayout.setRowStretchFactor(ROW_HOR_LINE, 0)
            if self.horPlotAdded:
                self.graphicsLayoutWidget.removeItem(self.horCrossPlotItem)
                self.horPlotAdded = False
                gridLayout.activate()

        if self.config.verCrossPlotCti.configValue:
            gridLayout.setColumnStretchFactor(COL_VER_LINE, 1)
            if not self.verPlotAdded:
                self.graphicsLayoutWidget.addItem(self.verCrossPlotItem, ROW_VER_LINE, COL_VER_LINE)
                self.verPlotAdded = True
                gridLayout.activate()
        else:
            gridLayout.setColumnStretchFactor(COL_VER_LINE, 0)
            if self.verPlotAdded:
                self.graphicsLayoutWidget.removeItem(self.verCrossPlotItem)
                self.verPlotAdded = False
                gridLayout.activate()

        self.horCrossPlotItem.invertX(self.config.xFlippedCti.configValue)
        self.verCrossPlotItem.invertY(self.config.yFlippedCti.configValue)

        if self.config.probeCti.configValue:
            self.probeLabel.setVisible(True)
            self.imagePlotItem.addItem(self.crossLineVertical, ignoreBounds=True)
            self.imagePlotItem.addItem(self.crossLineHorizontal, ignoreBounds=True)
        else:
            self.probeLabel.setVisible(False)

        self.config.updateTarget()


    def mouseMoved(self, viewPos):
        """ Updates the probe text with the values under the cursor.
            Draws a vertical line and a symbol at the position of the probe.
        """
        self.probeLabel.setText("<span style='color: #808080'>no data at cursor</span>")
        self.crossLineVertical.setVisible(False)
        self.crossLineHorizontal.setVisible(False)

        self.horPlotDataItem.setData(x=[], y=[])
        self.verPlotDataItem.setData(x=[], y=[])

        if self.slicedArray is not None and self.viewBox.sceneBoundingRect().contains(viewPos):

            scenePos = self.viewBox.mapSceneToView(viewPos)

            # We use int() to convert to integer, and not round(), because the image pixels
            # are drawn from (row, col) to (row + 1, col + 1). That is, their center is at
            # (row + 0.5, col + 0.5)
            row, col = int(scenePos.y()), int(scenePos.x())
            nRows, nCols = self.slicedArray.shape

            if (0 <= row < nRows) and (0 <= col < nCols):
                value = self.slicedArray[row, col]
                txt = "pos = ({:d}, {:d}), value = {!r}".format(row, col, value)
                self.probeLabel.setText(txt)

                # Show cross section at the cursor pos in the line plots
                if self.config.horCrossPlotCti.configValue:
                    self.crossLineHorizontal.setVisible(True)
                    self.crossLineHorizontal.setPos(row + 0.5) # Adding 0.5 to find the pixel center
                    self.horPlotDataItem.setData(self.slicedArray[row, :])

                if self.config.verCrossPlotCti.configValue:
                    self.crossLineVertical.setVisible(True)
                    self.crossLineVertical.setPos(col + 0.5) # Adding 0.5 to find the pixel center
                    try:
                        self.verPlotDataItem.setData(self.slicedArray[:, col], np.arange(nRows))
                    except Exception as ex:
                        # Occorred as a bug that I can't reproduce: the dataType don't match.
                        # If it occurs outside debugging we issue a warning.
                        # When a rec-array is plotted.
                        from pyqtgraph.graphicsItems.PlotDataItem import dataType
                        logger.warn("{} ?= {}".format(dataType(self.slicedArray[:, col]),
                                                      dataType(np.arange(nRows))))
                        if DEBUGGING:
                            raise
                        else:
                            logger.error(ex)

