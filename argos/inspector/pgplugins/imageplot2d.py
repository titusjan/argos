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

import logging, math
import numpy as np
import pyqtgraph as pg

from functools import partial
from collections import OrderedDict
from argos.info import DEBUGGING
from argos.config.boolcti import BoolCti, BoolGroupCti
from argos.config.choicecti import ChoiceCti
from argos.config.groupcti import MainGroupCti
from argos.inspector.abstract import AbstractInspector, InvalidDataError, UpdateReason
from argos.inspector.pgplugins.pgctis import (X_AXIS, Y_AXIS, BOTH_AXES, viewBoxAxisRange,
                                                 defaultAutoRangeMethods, PgAxisLabelCti,
                                                 PgAxisCti, PgAxisFlipCti, PgAspectRatioCti,
                                                 PgAxisRangeCti, PgHistLutColorRangeCti, PgGridCti,
                                                 PgGradientEditorItemCti, setXYAxesAutoRangeOn,
                                                 PgPlotDataItemCti)
from argos.inspector.pgplugins.pgplotitem import ArgosPgPlotItem
from argos.inspector.pgplugins.pghistlutitem import HistogramLUTItem
from argos.qt import Qt, QtCore, QtGui, QtSlot
from argos.utils.cls import array_has_real_numbers, check_class, is_an_array, to_string
from argos.utils.masks import replaceMaskedValueWithFloat, maskedNanPercentile, ArrayWithMask

logger = logging.getLogger(__name__)

ROW_TITLE,    COL_TITLE    = 0, 0  # colspan = 3
ROW_COLOR,    COL_COLOR    = 1, 0  # rowspan = 2
ROW_HOR_LINE, COL_HOR_LINE = 1, 1
ROW_IMAGE,    COL_IMAGE    = 2, 1
ROW_VER_LINE, COL_VER_LINE = 2, 2
ROW_PROBE,    COL_PROBE    = 3, 0  # colspan = 2



def calcPgImagePlot2dDataRange(pgImagePlot2d, percentage, crossPlot):
    """ Calculates the range from the inspectors' sliced array. Discards percentage of the minimum
        and percentage of the maximum values of the inspector.slicedArray

        :param pgImagePlot2d: the range methods will work on (the sliced array) of this inspector.
        :param percentage: percentage that will be discarded.
        :param crossPlot: if None, the range will be calculated from the entire sliced array,
            if "horizontal" or "vertical" the range will be calculated from the data under the
            horizontal or vertical cross hairs.
            If the cursor is outside the image, there is no valid data under the cross-hair and
            the range will be determined from the sliced array as a fall back.
    """
    check_class(pgImagePlot2d.slicedArray, ArrayWithMask) # sanity check

    if crossPlot is None:
        array = pgImagePlot2d.slicedArray  # the whole image

    elif crossPlot == 'horizontal':
        if pgImagePlot2d.crossPlotRow is not None:
            array = pgImagePlot2d.slicedArray.asMaskedArray()[pgImagePlot2d.crossPlotRow, :]
        else:
            array = pgImagePlot2d.slicedArray # fall back on complete sliced array

    elif crossPlot == 'vertical':
        if pgImagePlot2d.crossPlotCol is not None:
            array = pgImagePlot2d.slicedArray.asMaskedArray()[:, pgImagePlot2d.crossPlotCol]
        else:
            array = pgImagePlot2d.slicedArray # fall back on complete sliced array
    else:
        raise ValueError("crossPlot must be: None, 'horizontal' or 'vertical', got: {}"
                         .format(crossPlot))

    return maskedNanPercentile(array, (percentage, 100-percentage) )


def crossPlotAutoRangeMethods(pgImagePlot2d, crossPlot, intialItems=None):
    """ Creates an ordered dict with autorange methods for an PgImagePlot2d inspector.

        :param pgImagePlot2d: the range methods will work on (the sliced array) of this inspector.
        :param crossPlot: if None, the range will be calculated from the entire sliced array,
            if "horizontal" or "vertical" the range will be calculated from the data under the
            horizontal or vertical cross hairs
        :param intialItems: will be passed on to the  OrderedDict constructor.
    """
    rangeFunctions = OrderedDict({} if intialItems is None else intialItems)

    # If crossPlot is "horizontal" or "vertical" make functions that determine the range from the
    # data at the cross hair.
    if crossPlot:
        rangeFunctions['cross all data'] = partial(calcPgImagePlot2dDataRange, pgImagePlot2d,
                                                   0.0, crossPlot)
        for percentage in [0.1, 0.2, 0.5, 1, 2, 5, 10, 20]:
            label = "cross discard {}%".format(percentage)
            rangeFunctions[label] = partial(calcPgImagePlot2dDataRange, pgImagePlot2d,
                                            percentage, crossPlot)

    # Always add functions that determine the data from the complete sliced array.
    for percentage in [0.1, 0.2, 0.5, 1, 2, 5, 10, 20]:
        rangeFunctions['image all data'] = partial(calcPgImagePlot2dDataRange, pgImagePlot2d,
                                                   0.0, None)

        label = "image discard {}%".format(percentage)
        rangeFunctions[label] = partial(calcPgImagePlot2dDataRange, pgImagePlot2d,
                                        percentage, None)
    return rangeFunctions



class PgImagePlot2dCti(MainGroupCti):
    """ Configuration tree item for a PgImagePlot2dCti inspector
    """
    def __init__(self, pgImagePlot2d, nodeName):
        """ Constructor

            Maintains a link to the target pgImagePlot2d inspector, so that changes in the
            configuration can be applied to the target by simply calling the apply method.
            Vice versa, it can connect signals to the target.
        """
        super(PgImagePlot2dCti, self).__init__(nodeName)
        check_class(pgImagePlot2d, PgImagePlot2d)
        self.pgImagePlot2d = pgImagePlot2d
        imagePlotItem = self.pgImagePlot2d.imagePlotItem
        viewBox = imagePlotItem.getViewBox()

        self.insertChild(ChoiceCti('title', 0, editable=True,
                                   configValues=["{base-name} -- {name} {slices}",
                                                 "{name} {slices}", "{path} {slices}"]))
        #### Axes ####
        self.aspectLockedCti = self.insertChild(PgAspectRatioCti(viewBox))

        self.xAxisCti = self.insertChild(PgAxisCti('x-axis'))
        #xAxisCti.insertChild(PgAxisShowCti(imagePlotItem, 'bottom')) # disabled, seems broken
        self.xAxisCti.insertChild(PgAxisLabelCti(imagePlotItem, 'bottom', self.pgImagePlot2d.collector,
            defaultData=1, configValues=[PgAxisLabelCti.NO_LABEL, "{x-dim} [index]"]))
        self.xFlippedCti = self.xAxisCti.insertChild(PgAxisFlipCti(viewBox, X_AXIS))
        self.xAxisRangeCti = self.xAxisCti.insertChild(PgAxisRangeCti(viewBox, X_AXIS))

        self.yAxisCti = self.insertChild(PgAxisCti('y-axis'))
        #yAxisCti.insertChild(PgAxisShowCti(imagePlotItem, 'left'))  # disabled, seems broken
        self.yAxisCti.insertChild(PgAxisLabelCti(imagePlotItem, 'left', self.pgImagePlot2d.collector,
            defaultData=1, configValues=[PgAxisLabelCti.NO_LABEL, "{y-dim} [index]"]))
        self.yFlippedCti = self.yAxisCti.insertChild(PgAxisFlipCti(viewBox, Y_AXIS))
        self.yAxisRangeCti = self.yAxisCti.insertChild(PgAxisRangeCti(viewBox, Y_AXIS))

        #### Color scale ####

        colorAutoRangeFunctions = defaultAutoRangeMethods(self.pgImagePlot2d)

        self.histColorRangeCti = self.insertChild(
            PgHistLutColorRangeCti(pgImagePlot2d.histLutItem, colorAutoRangeFunctions,
                                   nodeName="color range"))

        histViewBox = pgImagePlot2d.histLutItem.vb
        histViewBox.enableAutoRange(Y_AXIS, False)
        rangeFunctions = defaultAutoRangeMethods(self.pgImagePlot2d,
            {PgAxisRangeCti.PYQT_RANGE: partial(viewBoxAxisRange, histViewBox, Y_AXIS)})

        self.histRangeCti = self.insertChild(
            PgAxisRangeCti(histViewBox, Y_AXIS, nodeName='histogram range',
                           autoRangeFunctions=rangeFunctions))

        self.insertChild(PgGradientEditorItemCti(self.pgImagePlot2d.histLutItem.gradient))

        # Probe and cross-hair plots
        self.probeCti = self.insertChild(BoolCti('show probe', True))

        self.crossPlotGroupCti = self.insertChild(BoolGroupCti('cross-hair',  expanded=False))

        self.crossPenCti = self.crossPlotGroupCti.insertChild(PgPlotDataItemCti(expanded=False))
        #self.crossLinesCti = self.crossPlotGroupCti.insertChild(PgPlotDataItemCti('cross pen',
        #                                                                          expanded=False))

        self.horCrossPlotCti = self.crossPlotGroupCti.insertChild(BoolCti('horizontal', False,
                                                                          expanded=False))
        self.horCrossPlotCti.insertChild(PgGridCti(pgImagePlot2d.horCrossPlotItem))
        self.horCrossPlotRangeCti = self.horCrossPlotCti.insertChild(PgAxisRangeCti(
            self.pgImagePlot2d.horCrossPlotItem.getViewBox(), Y_AXIS, nodeName="data range",
            autoRangeFunctions = crossPlotAutoRangeMethods(self.pgImagePlot2d, "horizontal")))

        self.verCrossPlotCti = self.crossPlotGroupCti.insertChild(BoolCti('vertical', False,
                                                                          expanded=False))
        self.verCrossPlotCti.insertChild(PgGridCti(pgImagePlot2d.verCrossPlotItem))
        self.verCrossPlotRangeCti = self.verCrossPlotCti.insertChild(PgAxisRangeCti(
            self.pgImagePlot2d.verCrossPlotItem.getViewBox(), X_AXIS, nodeName="data range",
            autoRangeFunctions = crossPlotAutoRangeMethods(self.pgImagePlot2d, "vertical")))

        # Connect signals
        self.pgImagePlot2d.imagePlotItem.sigAxisReset.connect(self.setImagePlotAutoRangeOn)
        self.pgImagePlot2d.horCrossPlotItem.sigAxisReset.connect(self.setHorCrossPlotAutoRangeOn)
        self.pgImagePlot2d.verCrossPlotItem.sigAxisReset.connect(self.setVerCrossPlotAutoRangeOn)

        # Also update axis auto range tree items when linked axes are resized
        horCrossViewBox = self.pgImagePlot2d.horCrossPlotItem.getViewBox()
        horCrossViewBox.sigRangeChangedManually.connect(self.xAxisRangeCti.setAutoRangeOff)
        verCrossViewBox = self.pgImagePlot2d.verCrossPlotItem.getViewBox()
        verCrossViewBox.sigRangeChangedManually.connect(self.yAxisRangeCti.setAutoRangeOff)


    def _closeResources(self):
        """ Disconnects signals.
            Is called by self.finalize when the cti is deleted.
        """
        verCrossViewBox = self.pgImagePlot2d.verCrossPlotItem.getViewBox()
        verCrossViewBox.sigRangeChangedManually.disconnect(self.yAxisRangeCti.setAutoRangeOff)
        horCrossViewBox = self.pgImagePlot2d.horCrossPlotItem.getViewBox()
        horCrossViewBox.sigRangeChangedManually.disconnect(self.xAxisRangeCti.setAutoRangeOff)

        self.pgImagePlot2d.verCrossPlotItem.sigAxisReset.disconnect(self.setVerCrossPlotAutoRangeOn)
        self.pgImagePlot2d.horCrossPlotItem.sigAxisReset.disconnect(self.setHorCrossPlotAutoRangeOn)
        self.pgImagePlot2d.imagePlotItem.sigAxisReset.disconnect(self.setImagePlotAutoRangeOn)


    @QtSlot(int)
    def setImagePlotAutoRangeOn(self, axisNumber):
        """ Sets the image plot's auto-range on for the axis with number axisNumber.

            :param axisNumber: 0 (X-axis), 1 (Y-axis), 2, (Both X and Y axes).
        """
        setXYAxesAutoRangeOn(self, self.xAxisRangeCti, self.yAxisRangeCti, axisNumber)


    @QtSlot(int)
    def setHorCrossPlotAutoRangeOn(self, axisNumber):
        """ Sets the horizontal cross-hair plot's auto-range on for the axis with number axisNumber.

            :param axisNumber: 0 (X-axis), 1 (Y-axis), 2, (Both X and Y axes).
        """
        setXYAxesAutoRangeOn(self, self.xAxisRangeCti, self.horCrossPlotRangeCti, axisNumber)


    @QtSlot(int)
    def setVerCrossPlotAutoRangeOn(self, axisNumber):
        """ Sets the vertical cross-hair plot's auto-range on for the axis with number axisNumber.

            :param axisNumber: 0 (X-axis), 1 (Y-axis), 2, (Both X and Y axes).
        """
        setXYAxesAutoRangeOn(self, self.verCrossPlotRangeCti, self.yAxisRangeCti, axisNumber)



class PgImagePlot2d(AbstractInspector):
    """ Inspector that contains a PyQtGraph 2-dimensional image plot.
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

        self.histLutItem = HistogramLUTItem() # what about GradientLegend?
        self.histLutItem.setImageItem(self.imageItem)
        self.histLutItem.vb.setMenuEnabled(False)
        self.histLutItem.setHistogramRange(0, 100) # Disables autoscaling

        # Probe and cross hair plots
        self.crossPlotRow = None # the row coordinate of the cross hair. None if no cross hair.
        self.crossPlotCol = None # the col coordinate of the cross hair. None if no cross hair.
        self.horCrossPlotItem = ArgosPgPlotItem()
        self.verCrossPlotItem = ArgosPgPlotItem()
        self.horCrossPlotItem.setXLink(self.imagePlotItem)
        self.verCrossPlotItem.setYLink(self.imagePlotItem)
        self.horCrossPlotItem.setLabel('left', ' ')
        self.verCrossPlotItem.setLabel('bottom', ' ')
        self.horCrossPlotItem.showAxis('top', True)
        self.horCrossPlotItem.showAxis('bottom', False)
        self.verCrossPlotItem.showAxis('right', True)
        self.verCrossPlotItem.showAxis('left', False)

        self.crossPen = pg.mkPen("#BFBFBF")
        self.crossShadowPen = pg.mkPen([0, 0, 0, 100], width=3)
        self.crossLineHorShadow = pg.InfiniteLine(angle=0, movable=False, pen=self.crossShadowPen)
        self.crossLineVerShadow = pg.InfiniteLine(angle=90, movable=False, pen=self.crossShadowPen)
        self.crossLineHorizontal = pg.InfiniteLine(angle=0, movable=False, pen=self.crossPen)
        self.crossLineVertical = pg.InfiniteLine(angle=90, movable=False, pen=self.crossPen)

        self.imagePlotItem.addItem(self.crossLineVerShadow, ignoreBounds=True)
        self.imagePlotItem.addItem(self.crossLineHorShadow, ignoreBounds=True)
        self.imagePlotItem.addItem(self.crossLineVertical, ignoreBounds=True)
        self.imagePlotItem.addItem(self.crossLineHorizontal, ignoreBounds=True)

        self.probeLabel = pg.LabelItem('', justify='left')

        # Layout

        # Hiding the horCrossPlotItem and horCrossPlotItem will still leave some space in the
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
        self._config = PgImagePlot2dCti(pgImagePlot2d=self, nodeName='2D image plot')

        # Connect signals
        # Based mouseMoved on crosshair.py from the PyQtGraph examples directory.
        # I did not use the SignalProxy because I did not see any difference.
        self.imagePlotItem.scene().sigMouseMoved.connect(self.mouseMoved)


    def finalize(self):
        """ Is called before destruction. Can be used to clean-up resources.
        """
        logger.debug("Finalizing: {}".format(self))
        self.imagePlotItem.scene().sigMouseMoved.disconnect(self.mouseMoved)
        self.imagePlotItem.close()
        self.graphicsLayoutWidget.close()


    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple(['Y', 'X'])


    def _hasValidData(self):
        """ Returns True if the inspector has data that can be plotted.
        """
        return self.slicedArray is not None and array_has_real_numbers(self.slicedArray.data)


    def _clearContents(self):
        """ Clears the contents when no valid data is available
        """
        logger.debug("Clearing inspector contents")
        self.titleLabel.setText('')

        # Don't clear the imagePlotItem, the imageItem is only added in the constructor.
        self.imageItem.clear()
        self.imagePlotItem.setLabel('left', '')
        self.imagePlotItem.setLabel('bottom', '')

        # Set the histogram range and levels to finite values to prevent futher errors if this
        # function was called after an exception in self.drawContents
        self.histLutItem.setHistogramRange(0, 100)
        self.histLutItem.setLevels(0, 100)

        self.crossPlotRow, self.crossPlotCol = None, None

        self.probeLabel.setText('')
        self.crossLineHorizontal.setVisible(False)
        self.crossLineVertical.setVisible(False)
        self.crossLineHorShadow.setVisible(False)
        self.crossLineVerShadow.setVisible(False)

        self.horCrossPlotItem.clear()
        self.verCrossPlotItem.clear()


    def _drawContents(self, reason=None, initiator=None):
        """ Draws the plot contents from the sliced array of the collected repo tree item.

            The reason parameter is used to determine if the axes will be reset (the initiator
            parameter is ignored). See AbstractInspector.updateContents for their description.
        """
        self.crossPlotRow = None # reset because the sliced array shape may change
        self.crossPlotCol = None # idem dito

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

        self.slicedArray = self.collector.getSlicedArray()

        if not self._hasValidData():
            self._clearContents()
            raise InvalidDataError("No data available or it does not contain real numbers")

        # -- Valid plot data from here on --

        # PyQtGraph doesn't handle masked array so we convert the masked values to Nans. Missing
        # data values are replaced by NaNs. The PyQtGraph image plot shows this as the color at the
        # lowest end of the color scale. Unfortunately we cannot choose a missing-value color, but
        # at least the Nans do not influence for the histogram and color range.
        # We don't update self.slicedArray here because the data probe should still be able to
        # print the actual value.
        imageArray = replaceMaskedValueWithFloat(self.slicedArray.data, self.slicedArray.mask,
                                                 np.nan, copyOnReplace=True)

        # Replace infinite value with Nans because PyQtGraph fails on them. WNote that the CTIs of
        # the cross plots (e.g. horCrossPlotRangeCti) are still connected to self.slicedArray, so
        # if the cross section consists of only infs, they may not able to update the autorange.
        # A warning is issued in that case.
        # We don't update self.slicedArray here because the data probe should still be able to
        # print the actual value.
        imageArray = replaceMaskedValueWithFloat(imageArray, np.isinf(self.slicedArray.data),
                                                 np.nan, copyOnReplace=True)

        # Reset the axes ranges (via the config)
        if (reason == UpdateReason.RTI_CHANGED or
            reason == UpdateReason.COLLECTOR_COMBO_BOX):
            self.config.xAxisRangeCti.autoRangeCti.data = True
            self.config.yAxisRangeCti.autoRangeCti.data = True
            self.config.histColorRangeCti.autoRangeCti.data = True
            self.config.histRangeCti.autoRangeCti.data = True
            self.config.horCrossPlotRangeCti.autoRangeCti.data = True
            self.config.verCrossPlotRangeCti.autoRangeCti.data = True

        # PyQtGraph uses the following dimension order: T, X, Y, Color.
        # We need to transpose the slicedArray ourselves because axes = {'x':1, 'y':0}
        # doesn't seem to do anything.
        imageArray = imageArray.transpose()
        self.imageItem.setImage(imageArray, autoLevels=False)

        self.horCrossPlotItem.invertX(self.config.xFlippedCti.configValue)
        self.verCrossPlotItem.invertY(self.config.yFlippedCti.configValue)

        self.probeLabel.setVisible(self.config.probeCti.configValue)

        self.titleLabel.setText(self.configValue('title').format(**self.collector.rtiInfo))

        # Update the config tree from the (possibly) new state of the PgImagePlot2d inspector,
        # e.g. the axis range or color range may have changed while drawing.
        self.config.updateTarget()


    @QtSlot(object)
    def mouseMoved(self, viewPos):
        """ Updates the probe text with the values under the cursor.
            Draws a vertical line and a symbol at the position of the probe.
        """
        try:
            check_class(viewPos, QtCore.QPointF)
            show_data_point = False # shows the data point as a circle in the cross hair plots
            self.crossPlotRow, self.crossPlotCol = None, None

            self.probeLabel.setText("<span style='color: #808080'>no data at cursor</span>")
            self.crossLineHorizontal.setVisible(False)
            self.crossLineVertical.setVisible(False)
            self.crossLineHorShadow.setVisible(False)
            self.crossLineVerShadow.setVisible(False)

            self.horCrossPlotItem.clear()
            self.verCrossPlotItem.clear()

            if (self._hasValidData() and self.slicedArray is not None
                and self.viewBox.sceneBoundingRect().contains(viewPos)):

                # Calculate the row and column at the cursor. We use math.floor because the pixel
                # corners of the image lie at integer values (and not the centers of the pixels).
                scenePos = self.viewBox.mapSceneToView(viewPos)
                row, col = math.floor(scenePos.y()), math.floor(scenePos.x())
                row, col = int(row), int(col) # Needed in Python 2
                nRows, nCols = self.slicedArray.shape

                if (0 <= row < nRows) and (0 <= col < nCols):
                    self.viewBox.setCursor(Qt.CrossCursor)

                    self.crossPlotRow, self.crossPlotCol = row, col
                    index = tuple([row, col])
                    valueStr = to_string(self.slicedArray[index],
                                         masked=self.slicedArray.maskAt(index),
                                         maskFormat='&lt;masked&gt;')
                    txt = "pos = ({:d}, {:d}), value = {}".format(row, col, valueStr)
                    self.probeLabel.setText(txt)

                    # Show cross section at the cursor pos in the line plots
                    if self.config.horCrossPlotCti.configValue:
                        self.crossLineHorShadow.setVisible(True)
                        self.crossLineHorizontal.setVisible(True)
                        self.crossLineHorShadow.setPos(row)
                        self.crossLineHorizontal.setPos(row)

                        # Line plot of cross section row.
                        # First determine which points are connected or separated by masks/nans.
                        rowData = self.slicedArray.data[row, :]
                        connected = np.isfinite(rowData)
                        if is_an_array(self.slicedArray.mask):
                            connected = np.logical_and(connected, ~self.slicedArray.mask[row, :])
                        else:
                            connected = (np.zeros_like(rowData)
                                         if self.slicedArray.mask else connected)

                        # Replace infinite value with nans because PyQtGraph can't handle them
                        rowData = replaceMaskedValueWithFloat(rowData, np.isinf(rowData),
                                                              np.nan, copyOnReplace=True)

                        horPlotDataItem = self.config.crossPenCti.createPlotDataItem()
                        horPlotDataItem.setData(rowData, connect=connected)
                        self.horCrossPlotItem.addItem(horPlotDataItem)

                        # Vertical line in hor-cross plot
                        crossLineShadow90 = pg.InfiniteLine(angle=90, movable=False,
                                                            pen=self.crossShadowPen)
                        crossLineShadow90.setPos(col)
                        self.horCrossPlotItem.addItem(crossLineShadow90, ignoreBounds=True)
                        crossLine90 = pg.InfiniteLine(angle=90, movable=False, pen=self.crossPen)
                        crossLine90.setPos(col)
                        self.horCrossPlotItem.addItem(crossLine90, ignoreBounds=True)

                        if show_data_point:
                            crossPoint90 = pg.PlotDataItem(symbolPen=self.crossPen)
                            crossPoint90.setSymbolBrush(QtGui.QBrush(self.config.crossPenCti.penColor))
                            crossPoint90.setSymbolSize(10)
                            crossPoint90.setData((col,), (rowData[col],))
                            self.horCrossPlotItem.addItem(crossPoint90, ignoreBounds=True)

                        self.config.horCrossPlotRangeCti.updateTarget() # update auto range
                        del rowData # defensive programming

                    if self.config.verCrossPlotCti.configValue:
                        self.crossLineVerShadow.setVisible(True)
                        self.crossLineVertical.setVisible(True)
                        self.crossLineVerShadow.setPos(col)
                        self.crossLineVertical.setPos(col)

                        # Line plot of cross section row.
                        # First determine which points are connected or separated by masks/nans.
                        colData = self.slicedArray.data[:, col]
                        connected = np.isfinite(colData)
                        if is_an_array(self.slicedArray.mask):
                            connected = np.logical_and(connected, ~self.slicedArray.mask[:, col])
                        else:
                            connected = (np.zeros_like(colData)
                                         if self.slicedArray.mask else connected)

                        # Replace infinite value with nans because PyQtGraph can't handle them
                        colData = replaceMaskedValueWithFloat(colData, np.isinf(colData),
                                                              np.nan, copyOnReplace=True)

                        verPlotDataItem = self.config.crossPenCti.createPlotDataItem()
                        verPlotDataItem.setData(colData, np.arange(nRows), connect=connected)
                        self.verCrossPlotItem.addItem(verPlotDataItem)

                        # Horizontal line in ver-cross plot
                        crossLineShadow0 = pg.InfiniteLine(angle=0, movable=False,
                                                           pen=self.crossShadowPen)
                        crossLineShadow0.setPos(row)
                        self.verCrossPlotItem.addItem(crossLineShadow0, ignoreBounds=True)
                        crossLine0 = pg.InfiniteLine(angle=0, movable=False, pen=self.crossPen)
                        crossLine0.setPos(row)
                        self.verCrossPlotItem.addItem(crossLine0, ignoreBounds=True)

                        if show_data_point:
                            crossPoint0 = pg.PlotDataItem(symbolPen=self.crossPen)
                            crossPoint0.setSymbolBrush(QtGui.QBrush(self.config.crossPenCti.penColor))
                            crossPoint0.setSymbolSize(10)
                            crossPoint0.setData((colData[row],), (row,))
                            self.verCrossPlotItem.addItem(crossPoint0, ignoreBounds=True)

                        self.config.verCrossPlotRangeCti.updateTarget() # update auto range
                        del colData # defensive programming

        except Exception as ex:
            # In contrast to _drawContents, this function is a slot and thus must not throw
            # exceptions. The exception is logged. Perhaps we should clear the cross plots, but
            # this could, in turn, raise exceptions.
            if DEBUGGING:
                raise
            else:
                logger.exception(ex)

