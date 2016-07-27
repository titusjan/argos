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

from functools import partial

from libargos.qt import QtGui
from libargos.info import DEBUGGING
from libargos.config.groupcti import MainGroupCti
from libargos.config.boolcti import BoolCti
from libargos.config.choicecti import ChoiceCti

from libargos.inspector.abstract import AbstractInspector, InvalidDataError
from libargos.inspector.pgplugins.pgctis import (X_AXIS, Y_AXIS, BOTH_AXES, viewBoxAxisRange,
                                                 defaultAutoRangeMethods, PgGridCti, PgAxisCti,
                                                 setXYAxesAutoRangeOn, PgAxisLabelCti,
                                                 PgAxisLogModeCti, PgAxisRangeCti, PgPlotDataItemCti)
from libargos.inspector.pgplugins.pgplotitem import ArgosPgPlotItem
from libargos.utils.cls import array_has_real_numbers, check_class


logger = logging.getLogger(__name__)

class PgLinePlot1dCti(MainGroupCti):
    """ Configuration tree for a PgLinePlot1d inspector
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
            defaultData=1, configValues=[PgAxisLabelCti.NO_LABEL, "{x-dim}"]))
        # No logarithmic X-Axis as long as abcissa is not yet implemented.
        #xAxisCti.insertChild(PgAxisLogModeCti(imagePlotItem, X_AXIS))
        self.xAxisRangeCti = self.xAxisCti.insertChild(PgAxisRangeCti(viewBox, X_AXIS))

        self.yAxisCti = self.insertChild(PgAxisCti('y-axis'))
        self.yAxisCti.insertChild(PgAxisLabelCti(plotItem, 'left', self.pgLinePlot1d.collector,
            defaultData=1, configValues=[PgAxisLabelCti.NO_LABEL, "{name} {unit}", "{path} {unit}",
                                         "{name}", "{path}", "{raw-unit}"]))
        self.yAxisCti.insertChild(PgAxisLogModeCti(plotItem, Y_AXIS))

        rangeFunctions = defaultAutoRangeMethods(self.pgLinePlot1d,
            {PgAxisRangeCti.PYQT_RANGE: partial(viewBoxAxisRange, viewBox, Y_AXIS)})
        self.yAxisRangeCti = self.yAxisCti.insertChild(PgAxisRangeCti(viewBox, Y_AXIS,
                                                                      rangeFunctions))

        #### Pen ####

        self.plotDataItemCti = self.insertChild(PgPlotDataItemCti())
        self.probeCti = self.insertChild(BoolCti('show probe', True))


        # Connect signals
        self._setAutoRangeOnFn = partial(setXYAxesAutoRangeOn, self,
                                         self.xAxisRangeCti, self.yAxisRangeCti)
        self.pgLinePlot1d.plotItem.sigAxisReset.connect(self._setAutoRangeOnFn)


    def _closeResources(self):
       """ Disconnects signals.
           Is called by self.finalize when the cti is deleted.
       """
       self.pgLinePlot1d.plotItem.sigAxisReset.disconnect(self._setAutoRangeOnFn)



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

        # The actual plot item.

        self.plotItem = ArgosPgPlotItem(contextMenu=self.contextMenu)
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
        self._config = PgLinePlot1dCti(pgLinePlot1d=self, nodeName='inspector') # TODO: should be able to change nodeName without --reset

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


    def _clearContents(self):
        """ Clears the  the inspector widget when no valid input is available.
        """
        self.titleLabel.setText('')
        self.plotItem.clear()
        self.plotItem.setLabel('left', '')
        self.plotItem.setLabel('bottom', '')



    def _drawContents(self, reason=None, initiator=None):
        """ Draws the plot contents from the sliced array of the collected repo tree item.

            The reason and initiator parameters are ignored.
            See AbstractInspector.updateContents for their description.
        """
        self.slicedArray = self.collector.getSlicedArray()

        if self.slicedArray is None or not array_has_real_numbers(self.slicedArray):
            self._clearContents()
            raise InvalidDataError("No data available or it does not contain real numbers")

        # Valid plot data here
        self.plotItem.clear()

        self.titleLabel.setText(self.configValue('title').format(**self.collector.rtiInfo))

        plotDataItem = self.config.plotDataItemCti.createPlotDataItem()
        plotDataItem.setData(self.slicedArray)
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


    def mouseMoved(self, viewPos):
        """ Updates the probe text with the values under the cursor.
            Draws a vertical line and a symbol at the position of the probe.
        """
        if (not self.config.probeCti.configValue or
            not self.viewBox.sceneBoundingRect().contains(viewPos)):

            self.crossLineVerShadow.setVisible(False)
            self.crossLineVertical.setVisible(False)
            self.probeLabel.setText("")
            self.probeDataItem.clear()
        else:
            scenePos = self.viewBox.mapSceneToView(viewPos)
            index = int(scenePos.x())

            if self.slicedArray is not None and 0 <= index < len(self.slicedArray):
                txt = "pos = {!r}, value = {!r}".format(index, self.slicedArray[index])
                self.probeLabel.setText(txt)
                self.crossLineVerShadow.setVisible(True)
                self.crossLineVerShadow.setPos(index)
                self.crossLineVertical.setVisible(True)
                self.crossLineVertical.setPos(index)
                self.probeDataItem.setData((index,), (self.slicedArray[index],))
            else:
                txt = "<span style='color: grey'>no data at cursor</span>"
                self.probeLabel.setText(txt)
                self.crossLineVerShadow.setVisible(False)
                self.crossLineVertical.setVisible(False)
                self.probeDataItem.clear()



