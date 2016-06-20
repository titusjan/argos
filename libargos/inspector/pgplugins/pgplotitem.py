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

from libargos.qt import Qt, QtCore, QtGui, QtSignal

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

DEFAULT_BORDER_PEN = pg.mkPen("#000000", width=1)


class ArgosPgPlotItem(PlotItem):
    """ Wrapper arround pyqtgraph.graphicsItems.PlotItem
        Overrides the autoBtnClicked method.
        Middle mouse click

        The menu is disabled by default. All settings I want can be set using the config tree;
        the other settings I don't want to support.

        Autorange is disabled by default as it is expected that the (viewbox of the) plot item will
        be connected to a PgAxisRangeCti that controls the (auto)range.

        Adds a black border of width 1.

        Sets the cursros to a cross inside the viewbox.
    """
    axisReset = QtSignal(int)

    def __init__(self,
                 enableMenu=False,
                 enableAutoRange=False,
                 borderPen=DEFAULT_BORDER_PEN,
                 *args, **kwargs):
        """ Constructor.
            :param enableMenu: if True right-click opens a context menu (default=False)
            :param borderPen: pen for drawing the viewBox border. Default black and width of 1.
        """
        super(ArgosPgPlotItem, self).__init__(enableMenu=enableMenu, *args, **kwargs)

        viewBox = self.getViewBox()
        viewBox.border = borderPen
        viewBox.setCursor(Qt.CrossCursor)
        viewBox.disableAutoRange(BOTH_AXES)

        # # Install event filters to catch double clicks
        # xAxisItem = self.getAxis('bottom')
        # xAxisItem.installEventFilter(self)



    def close(self):
        """ Is called before destruction. Can be used to clean-up resources
            Could be called 'finalize' but PlotItem already has a close so we reuse that.
        """
        logger.debug("Finalizing: {}".format(self))
        # xAxisItem = self.getAxis('bottom')
        # xAxisItem.removeEventFilter(self)

        super(ArgosPgPlotItem, self).close()


    def autoBtnClicked(self):
        """ Hides the button but does not enable/disable autorange.
            That will be done by PgAxisRangeCti
        """ # TODO: use axisReset.
        logger.debug("ArgosPgPlotItem.autoBtnClicked, mode:{}".format(self.autoBtn.mode))
        if self.autoBtn.mode == 'auto':
            self.autoBtn.hide()

        self.axisReset.emit(BOTH_AXES)


    def mouseClickEvent(self, ev):
        """ If the middle mouse button is clicked the axis are reset.
        """
        if ev.button() == QtCore.Qt.MiddleButton:
            logger.debug("Clicked middle mouse. Emitting sigClicked")
            ev.accept()
            self.axisReset.emit(BOTH_AXES)


    # Does not work (yet). Most likely because the linked viewbox is also included in the
    # boundingRect, so that clicks in the viewbox also trigger the range reset.
    # def eventFilter(self, watchedObject, event):
    #     """ Filters events from the AxisItems so that a middle mouse click reset the range of
    #         that axis.
    #     """
    #     logger.debug("intercepting {}: {} eventType={}".format(watchedObject, type(event), event.type()))
    #     if type(event) == QtGui.QGraphicsSceneMouseEvent:
    #
    #         if event.button() == Qt.MiddleButton:
    #             #assert False, "stopped here"
    #             logger.debug("event button={}, emitting axisReset".format(event.button()))
    #             self.axisReset.emit(X_AXIS)
    #             return True
    #
    #     return super(ArgosPgPlotItem, self).eventFilter(watchedObject, event)
    #


