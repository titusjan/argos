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
import numpy as np
import pyqtgraph as pg

from functools import partial

from argos.qt import QtCore, QtGui, QtSlot
from argos.info import DEBUGGING
from argos.config.groupcti import MainGroupCti
from argos.config.boolcti import BoolCti
from argos.config.choicecti import ChoiceCti

from argos.inspector.abstract import AbstractInspector, InvalidDataError, UpdateReason
from argos.inspector.pgplugins.pgctis import (X_AXIS, Y_AXIS, viewBoxAxisRange,
                                              defaultAutoRangeMethods, PgGridCti, PgAxisCti,
                                              setXYAxesAutoRangeOn, PgAxisLabelCti,
                                              PgAxisLogModeCti, PgAxisRangeCti, PgPlotDataItemCti)
from argos.inspector.pgplugins.pgplotitem import ArgosPgPlotItem
from argos.utils.cls import (array_has_real_numbers, check_class, fill_values_to_nan,
                                is_an_array, check_is_an_array, to_string)
from argos.utils.masks import replaceMaskedValue


logger = logging.getLogger(__name__)

class PgLinePlot1dCti(MainGroupCti):
    """ Configuration tree item for a PgLinePlot1d inspector
    """
    def __init__(self, pgLinePlot1d, nodeName):
        """ Constructor

            Maintains a link to the target pgLinePlot1d inspector, so that changes in the
            configuration can be applied to the target by simply calling the apply method.
            Vice versa, it can connect signals to the target.
        """
        super(PgLinePlot1dCti, self).__init__(nodeName=nodeName)

        check_class(pgLinePlot1d, PgLinePlot1d)
        self.pgLinePlot1d = pgLinePlot1d

        self.insertChild(ChoiceCti('title', 0, editable=True,
                                    configValues=["{base-name} -- {name} {slices}",
                                                  "{name} {slices}", "{path} {slices}"]))

        #### Axes ####
        plotItem = self.pgLinePlot1d.plotItem
        viewBox = plotItem.getViewBox()

        self.insertChild(PgGridCti(plotItem))

        self.xAxisCti = self.insertChild(PgAxisCti('x-axis'))
        self.xAxisCti.insertChild(PgAxisLabelCti(plotItem, 'bottom', self.pgLinePlot1d.collector,
            defaultData=1, configValues=[PgAxisLabelCti.NO_LABEL, "{x-dim} [index]"]))
        # No logarithmic X-Axis as long as abcissa is not yet implemented.
        #xAxisCti.insertChild(PgAxisLogModeCti(imagePlotItem, X_AXIS))
        self.xAxisRangeCti = self.xAxisCti.insertChild(PgAxisRangeCti(viewBox, X_AXIS))

        self.yAxisCti = self.insertChild(PgAxisCti('y-axis'))
        self.yAxisCti.insertChild(PgAxisLabelCti(plotItem, 'left', self.pgLinePlot1d.collector,
            defaultData=1, configValues=[PgAxisLabelCti.NO_LABEL, "{name} {unit}", "{path} {unit}",
                                         "{name}", "{path}", "{raw-unit}"]))
        self.yLogCti = self.yAxisCti.insertChild(PgAxisLogModeCti(plotItem, Y_AXIS))

        rangeFunctions = defaultAutoRangeMethods(self.pgLinePlot1d,
            {PgAxisRangeCti.PYQT_RANGE: partial(viewBoxAxisRange, viewBox, Y_AXIS)})
        self.yAxisRangeCti = self.yAxisCti.insertChild(PgAxisRangeCti(viewBox, Y_AXIS,
                                                                      rangeFunctions))

        #### Pen ####

        self.plotDataItemCti = self.insertChild(PgPlotDataItemCti())
        self.probeCti = self.insertChild(BoolCti('show probe', True))

        # Connect signals
        self.pgLinePlot1d.plotItem.sigAxisReset.connect(self.setAutoRangeOn)


    def _closeResources(self):
       """ Disconnects signals.
           Is called by self.finalize when the cti is deleted.
       """
       self.pgLinePlot1d.plotItem.sigAxisReset.disconnect(self.setAutoRangeOn)


    @QtSlot(int)
    def setAutoRangeOn(self, axisNumber):
        """ Sets the auto-range of the axis on.

            :param axisNumber: 0 (X-axis), 1 (Y-axis), 2, (Both X and Y axes).
        """
        setXYAxesAutoRangeOn(self, self.xAxisRangeCti, self.yAxisRangeCti, axisNumber)



class PgLinePlot1d(AbstractInspector):
    """ Inspector that contains a PyQtGraph 1-dimensional line plot
    """
    def __init__(self, collector, parent=None):
        """ Constructor. See AbstractInspector constructor for parameters.
        """
        super(PgLinePlot1d, self).__init__(collector, parent=parent)

        # The sliced array is kept in memory. This may be different per inspector, e.g. 3D
        # inspectors may decide that this uses to much memory. The slice is therefor not stored
        # in the collector.
        self.slicedArray = None

        self.graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self.contentsLayout.addWidget(self.graphicsLayoutWidget)
        self.titleLabel = self.graphicsLayoutWidget.addLabel('<plot title goes here>', 0, 0)

        self.plotItem = ArgosPgPlotItem()
        self.viewBox = self.plotItem.getViewBox()
        self.graphicsLayoutWidget.addItem(self.plotItem, 1, 0)

        # Probe
        probePen = pg.mkPen("#BFBFBF")
        probeShadowPen = pg.mkPen("#00000064", width=3)
        self.crossLineVerShadow = pg.InfiniteLine(angle=90, movable=False, pen=probeShadowPen)
        self.crossLineVertical = pg.InfiniteLine(angle=90, movable=False, pen=probePen)
        self.probeDataItem = pg.PlotDataItem(symbolPen=probePen)
        self.probeLabel = self.graphicsLayoutWidget.addLabel('', 2, 0, justify='left')

        # Configuration tree
        self._config = PgLinePlot1dCti(pgLinePlot1d=self, nodeName='1D line plot')

        # Connect signals
        # Based mouseMoved on crosshair.py from the PyQtGraph examples directory.
        # I did not use the SignalProxy because I did not see any difference.
        self.plotItem.scene().sigMouseMoved.connect(self.mouseMoved)


    def finalize(self):
        """ Is called before destruction. Can be used to clean-up resources
        """
        logger.debug("Finalizing: {}".format(self))
        self.plotItem.scene().sigMouseMoved.disconnect(self.mouseMoved)
        self.plotItem.close()
        self.graphicsLayoutWidget.close()


    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple(['X'])


    def _hasValidData(self):
        """ Returns True if the inspector has data that can be plotted.
        """
        return self.slicedArray is not None and array_has_real_numbers(self.slicedArray.data)


    def _clearContents(self):
        """ Clears the  the inspector widget when no valid input is available.
        """
        self.titleLabel.setText('')
        self.plotItem.clear()
        self.plotItem.setLabel('left', '')
        self.plotItem.setLabel('bottom', '')


    def _drawContents(self, reason=None, initiator=None):
        """ Draws the plot contents from the sliced array of the collected repo tree item.

            The reason parameter is used to determine if the axes will be reset (the initiator
            parameter is ignored). See AbstractInspector.updateContents for their description.
        """
        self.slicedArray = self.collector.getSlicedArray()

        if not self._hasValidData():
            self._clearContents()
            raise InvalidDataError("No data available or it does not contain real numbers")

        # -- Valid plot data from here on --

        # PyQtGraph doesn't handle masked arrays so we convert the masked values to Nans (missing
        # data values are replaced by NaNs). The PyQtGraph line plot omits the Nans, which is great.
        self.slicedArray.replaceMaskedValueWithNan()  # will convert data to float if int

        self.plotItem.clear()

        # Reset the axes ranges (via the config)
        if (reason == UpdateReason.RTI_CHANGED or
            reason == UpdateReason.COLLECTOR_COMBO_BOX):

            # self.config.yAxisRangeCti.setAutoRangeOn() doesn't work as refreshBlocked is True
            # TODO: can refreshBlocked maybe only block the signals to prevent loops?
            self.config.xAxisRangeCti.autoRangeCti.data = True
            self.config.yAxisRangeCti.autoRangeCti.data = True

        self.titleLabel.setText(self.configValue('title').format(**self.collector.rtiInfo))

        connected = np.isfinite(self.slicedArray.data)
        if is_an_array(self.slicedArray.mask):
            connected = np.logical_and(connected, ~self.slicedArray.mask)
        else:
            connected = np.zeros_like(self.slicedArray.data) if self.slicedArray.mask else connected

        plotDataItem = self.config.plotDataItemCti.createPlotDataItem()
        plotDataItem.setData(self.slicedArray.data, connect=connected)

        self.plotItem.addItem(plotDataItem)

        if self.config.probeCti.configValue:
            self.probeLabel.setVisible(True)
            self.plotItem.addItem(self.crossLineVerShadow, ignoreBounds=True)
            self.plotItem.addItem(self.crossLineVertical, ignoreBounds=True)
            self.plotItem.addItem(self.probeDataItem, ignoreBounds=True)
            self.probeDataItem.setSymbolBrush(QtGui.QBrush(self.config.plotDataItemCti.penColor))
            self.probeDataItem.setSymbolSize(10)
        else:
            self.probeLabel.setVisible(False)

        # Update the config tree from the (possibly) new state of the PgLinePlot1d inspector,
        # e.g. the axis range may have changed while drawing.
        self.config.updateTarget()


    @QtSlot(object)
    def mouseMoved(self, viewPos):
        """ Updates the probe text with the values under the cursor.
            Draws a vertical line and a symbol at the position of the probe.
        """
        try:
            check_class(viewPos, QtCore.QPointF)
            self.crossLineVerShadow.setVisible(False)
            self.crossLineVertical.setVisible(False)
            self.probeLabel.setText("")
            self.probeDataItem.clear()

            if (self._hasValidData() and self.config.probeCti.configValue and
                self.viewBox.sceneBoundingRect().contains(viewPos)):

                scenePos = self.viewBox.mapSceneToView(viewPos)
                index = int(scenePos.x())
                data = self.slicedArray.data

                if not 0 <= index < len(data):
                    txt = "<span style='color: grey'>no data at cursor</span>"
                    self.probeLabel.setText(txt)
                else:
                    valueStr = to_string(data[index], masked=self.slicedArray.maskAt(index),
                                         maskFormat='&lt;masked&gt;')
                    self.probeLabel.setText("pos = {!r}, value = {}".format(index, valueStr))
                    if np.isfinite(data[index]):
                        self.crossLineVerShadow.setVisible(True)
                        self.crossLineVerShadow.setPos(index)
                        self.crossLineVertical.setVisible(True)
                        self.crossLineVertical.setPos(index)
                        if data[index] > 0 or self.config.yLogCti.configValue == False:
                            self.probeDataItem.setData((index,), (data[index],))

        except Exception as ex:
            # In contrast to _drawContents, this function is a slot and thus must not throw
            # exceptions. The exception is logged. Perhaps we should clear the cross plots, but
            # this could, in turn, raise exceptions.
            if DEBUGGING:
                raise
            else:
                logger.exception(ex)

