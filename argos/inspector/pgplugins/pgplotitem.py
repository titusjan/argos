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

from argos.info import DEBUGGING
from argos.qt import Qt, QtCore, QtWidgets, QtSignal

logger = logging.getLogger(__name__)

from pyqtgraph.graphicsItems.PlotItem import PlotItem


X_AXIS = pg.ViewBox.XAxis
Y_AXIS = pg.ViewBox.YAxis
BOTH_AXES = pg.ViewBox.XYAxes
VALID_AXES_NUMBERS = (X_AXIS, Y_AXIS, BOTH_AXES)

DEFAULT_BORDER_PEN = pg.mkPen("#000000", width=1)


class ArgosPgPlotItem(PlotItem):
    """ Wrapper around pyqtgraph.graphicsItems.PlotItem

        Overrides the autoBtnClicked method.
        Middle mouse click resets the axis.

        The original PyQtGraph menu is disabled (all settings I want can be set using the config
        tree; the other settings I don't want to support). Furthermore a context menu is created
        that allows the user to rescale the axes.

        Autorange is disabled as it is expected that the (viewbox of the) plot item will be
        connected to two PgAxisRangeCti objects that control the (auto)range of the X and Y axes.

        Adds a black border of width 1.

        Sets the cursor to a cross if it's inside the viewbox.
    """

    # Use a QueuedConnection to connect to sigResetAxis so that the reset is scheduled after all
    # current events have been processed. Otherwise the mouseReleaseEvent may look for a
    # PlotCurveItem that is no longer present after the reset, which results in a RuntimeError:
    # wrapped C/C++ object of type PlotCurveItem has been deleted.
    sigResetAxis = QtSignal(int)

    def __init__(self,
                 borderPen=DEFAULT_BORDER_PEN,
                 *args, **kwargs):
        """ Constructor.

            :param borderPen: pen for drawing the viewBox border. Default black and width of 1.
        """
        super(ArgosPgPlotItem, self).__init__(*args, **kwargs)

        self.setMenuEnabled(False)
        #pg.setConfigOption('leftButtonPan', False)

        viewBox = self.getViewBox()
        viewBox.border = borderPen
        viewBox.setCursor(Qt.CrossCursor)
        viewBox.disableAutoRange(BOTH_AXES)
        viewBox.mouseClickEvent = lambda ev: self._axesMouseClickEvent(ev, BOTH_AXES)

        # Color of zoom-rectangle.
        alpha = 100
        greyVal = 160
        viewBox.rbScaleBox.setPen(pg.mkPen((0, 0, 0, alpha), width=2))
        viewBox.rbScaleBox.setBrush(pg.mkBrush(greyVal, greyVal, greyVal, alpha))

        # Add mouseClickEvent event handlers to the X and Y axis. This allows for resetting
        # the scale of each axes separately by middle mouse clicking the axis.
        for xAxisItem in (self.getAxis('bottom'), self.getAxis('top')):
            xAxisItem.mouseClickEvent = lambda ev: self._axesMouseClickEvent(ev, X_AXIS)
            xAxisItem.setCursor(Qt.SizeHorCursor)

        for yAxisItem in (self.getAxis('left'), self.getAxis('right')):
            yAxisItem.mouseClickEvent = lambda ev: self._axesMouseClickEvent(ev, Y_AXIS)
            yAxisItem.setCursor(Qt.SizeVerCursor)

        self.resetAxesAction = QtWidgets.QAction("Reset Axes", self,
                                 triggered = lambda: self.emitResetAxisSignal(BOTH_AXES),
                                 toolTip = "Resets the zoom factor of the X-axis and Y-axis")
        self.addAction(self.resetAxesAction)

        self.resetXAxisAction = QtWidgets.QAction("Reset X-axis", self,
                                 triggered = lambda: self.emitResetAxisSignal(X_AXIS),
                                 toolTip = "Resets the zoom factor of the X-axis")
        self.addAction(self.resetXAxisAction)

        self.resetYAxisAction = QtWidgets.QAction("Reset Y-axis", self,
                                 triggered = lambda: self.emitResetAxisSignal(Y_AXIS),
                                 toolTip = "Resets the zoom factor of the Y-axis")
        self.addAction(self.resetYAxisAction)



    def close(self):
        """ Is called before destruction. Can be used to clean-up resources
            Could be called 'finalize' but PlotItem already has a close so we reuse that.
        """
        logger.debug("Finalizing: {}".format(self))
        super(ArgosPgPlotItem, self).close()


    def _axesMouseClickEvent(self, mouseClickEvent, axisNumber):
        """ Handles the mouse clicks events when clicked on the axes or in the central viewbox

            :param mouseClickEvent: pyqtgraph.GraphicsScene.mouseEvents.MouseClickEvent
            :param axisNumber: the axis (X=0, Y=1, both=2)

            Emits sigResetAxis when the middle mouse button is clicked.
        """
        if mouseClickEvent.button() == QtCore.Qt.MiddleButton:
            mouseClickEvent.accept()
            self.emitResetAxisSignal(axisNumber)


    def mouseClickEvent(self, mouseClickEvent):
        """ Handles (PyQtGraph) mouse click events.

            Opens the context menu if a right mouse button was clicked. (We can't simply use
            setContextMenuPolicy(Qt.ActionsContextMenu because the PlotItem class does not derive
            from QWidget).

            :param mouseClickEvent: pyqtgraph.GraphicsScene.mouseEvents.MouseClickEvent
        """
        if mouseClickEvent.button() == QtCore.Qt.RightButton:
            contextMenu = QtWidgets.QMenu()
            for action in self.actions():
                contextMenu.addAction(action)

            screenPos = mouseClickEvent.screenPos() # Screenpos is a QPointF, convert to QPoint.
            screenX = round(screenPos.x())
            screenY = round(screenPos.y())
            contextMenu.exec_(QtCore.QPoint(screenX, screenY))


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
                logger.warning(msg)

        logger.debug("Emitting sigResetAxis({}) for {!r}".format(axisNumber, self))
        self.sigResetAxis.emit(axisNumber)


    def setRectangleZoomOn(self, boolean):
        """ Turns on rectangle zoom mode.

            In rectangle zoom mode, the left mouse drag draws a rectangle, which defines the new
            view limits. In panning mode (the default), a left mouse drag will pan the scene.

            :param boolean: if True plotting is set to 'rect'
        """
        viewbox = self.getViewBox()
        if boolean:
            viewbox.setMouseMode(pg.ViewBox.RectMode)
        else:
            viewbox.setMouseMode(pg.ViewBox.PanMode)
