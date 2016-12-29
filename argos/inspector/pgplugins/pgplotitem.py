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

""" Module that contains ArgosPgPlotItem.
"""
from __future__ import division, print_function

import logging
import pyqtgraph as pg

from functools import partial
from argos.info import DEBUGGING
from argos.qt import Qt, QtCore, QtWidgets, QtSignal

logger = logging.getLogger(__name__)

USE_SIMPLE_PLOT = False

if USE_SIMPLE_PLOT:
    # An experimental simplification of PlotItem. Not included in the distribution
    logger.warn("Using SimplePlotItem as PlotItem")
    from pyqtgraph.graphicsItems.PlotItem.simpleplotitem import SimplePlotItem as PlotItem
else:
    from pyqtgraph.graphicsItems.PlotItem import PlotItem


X_AXIS = pg.ViewBox.XAxis
Y_AXIS = pg.ViewBox.YAxis
BOTH_AXES = pg.ViewBox.XYAxes
VALID_AXES_NUMBERS = (X_AXIS, Y_AXIS, BOTH_AXES)

DEFAULT_BORDER_PEN = pg.mkPen("#000000", width=1)


def middleMouseClickEvent(argosPgPlotItem, axisNumber, mouseClickEvent):
    """ Emits sigAxisReset when the middle mouse button is clicked on an axis of the the plot item.
    """
    if mouseClickEvent.button() == QtCore.Qt.MiddleButton:
        mouseClickEvent.accept()
        argosPgPlotItem.emitResetAxisSignal(axisNumber)



class ArgosPgPlotItem(PlotItem):
    """ Wrapper arround pyqtgraph.graphicsItems.PlotItem
        Overrides the autoBtnClicked method.
        Middle mouse click

        The original PyQtGraph menu is disabled. All settings I want can be set using the config
        tree; the other settings I don't want to support. Furthermore a context menu is created
        that allows the user to rescale the axes.

        Autorange is disabled as it is expected that the (viewbox of the) plot item will be
        connected to two PgAxisRangeCti objects that control the (auto)range of the X and Y axes.

        Adds a black border of width 1.

        Sets the cursor to a cross if it's inside the viewbox.
    """
    sigAxisReset = QtSignal(int)

    def __init__(self,
                 borderPen=DEFAULT_BORDER_PEN,
                 *args, **kwargs):
        """ Constructor.
            :param enableMenu: if True right-click opens a context menu (default=False)
            :param borderPen: pen for drawing the viewBox border. Default black and width of 1.
        """
        super(ArgosPgPlotItem, self).__init__(*args, **kwargs)

        viewBox = self.getViewBox()
        viewBox.border = borderPen
        viewBox.setCursor(Qt.CrossCursor)
        viewBox.disableAutoRange(BOTH_AXES)
        viewBox.mouseClickEvent = partial(middleMouseClickEvent, self, BOTH_AXES)

        # Add mouseClickEvent event handlers to the X and Y axis. This allows for resetting
        # the scale of each axes separately by middle mouse clicking the axis.
        for xAxisItem in (self.getAxis('bottom'), self.getAxis('top')):
            xAxisItem.mouseClickEvent = partial(middleMouseClickEvent, self, X_AXIS)
            xAxisItem.setCursor(Qt.SizeHorCursor)

        for yAxisItem in (self.getAxis('left'), self.getAxis('right')):
            yAxisItem.mouseClickEvent = partial(middleMouseClickEvent, self, Y_AXIS)
            yAxisItem.setCursor(Qt.SizeVerCursor)

        # Context menu with actions to reset the zoom.
        #self.setContextMenuPolicy(Qt.ActionsContextMenu)

        self.resetAxesAction = QtWidgets.QAction("Reset Axes", self,
                                 triggered = lambda: self.emitResetAxisSignal(BOTH_AXES),
                                 statusTip = "Resets the zoom factor of the X-axis and Y-axis")
        self.addAction(self.resetAxesAction)

        self.resetXAxisAction = QtWidgets.QAction("Reset X-axis", self,
                                 triggered = lambda: self.emitResetAxisSignal(X_AXIS),
                                 statusTip = "Resets the zoom factor of the X-axis")
        self.addAction(self.resetXAxisAction)

        self.resetYAxisAction = QtWidgets.QAction("Reset Y-axis", self,
                                 triggered = lambda: self.emitResetAxisSignal(Y_AXIS),
                                 statusTip = "Resets the zoom factor of the Y-axis")
        self.addAction(self.resetYAxisAction)


    def close(self):
        """ Is called before destruction. Can be used to clean-up resources
            Could be called 'finalize' but PlotItem already has a close so we reuse that.
        """
        logger.debug("Finalizing: {}".format(self))
        super(ArgosPgPlotItem, self).close()


    def contextMenuEvent(self, event):
        """ Shows the context menu at the cursor position

            We need to take the event-based approach because ArgosPgPlotItem does derives from
            QGraphicsWidget, and not from QWidget, and therefore doesn't have the
            customContextMenuRequested signal.
        """
        contextMenu = QtWidgets.QMenu()
        for action in self.actions():
            contextMenu.addAction(action)
        contextMenu.exec_(event.screenPos())


    def autoBtnClicked(self):
        """ Hides the button but does not enable/disable autorange.
            That will be done by PgAxisRangeCti
        """
        self.resetAxesAction.trigger()


    def emitResetAxisSignal(self, axisNumber):
        """ Emits the sigResetAxis with the axisNumber as parameter
            axisNumber should be 0 for X, 1 for Y, and 2 for both axes.
        """
        assert axisNumber in (VALID_AXES_NUMBERS), \
            "Axis Nr should be one of {}, got {}".format(VALID_AXES_NUMBERS, axisNumber)

        # Hide 'auto-scale (A)' button
        logger.debug("ArgosPgPlotItem.autoBtnClicked, mode:{}".format(self.autoBtn.mode))
        if self.autoBtn.mode == 'auto':
            self.autoBtn.hide()
        else:
            # Does this occur?
            msg = "Unexpected autobutton mode: {}".format(self.autoBtn.mode)
            if DEBUGGING:
                raise ValueError(msg)
            else:
                logger.warn(msg)

        logger.debug("Emitting sigAxisReset({}) for {!r}".format(axisNumber, self))
        self.sigAxisReset.emit(axisNumber)

