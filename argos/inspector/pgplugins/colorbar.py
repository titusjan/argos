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

""" Module that contains ArgosPgColorBar.
"""
from __future__ import division, print_function

import logging
import warnings

import pyqtgraph as pg

from argos.qt import QtCore, QtWidgets, QtSignal


from argos.utils.cls import check_class
from pgcolorbar.colorlegend import ColorLegendItem

# from argos.info import DEBUGGING
# from argos.qt import Qt, QtCore, QtWidgets, QtSignal

logger = logging.getLogger(__name__)

warnings.filterwarnings(action='default', category=RuntimeWarning, module='pgcolorbar.colorlegend')  # Show once


class ArgosColorLegendItem(ColorLegendItem):
    """ Wrapper around pgcolorbar.colorlegend.ColorLegendItem.

        Suppresses the FutureWarning of PyQtGraph in _updateHistogram.
        Overrides the _imageItemHasIntegerData method.
        Adds context menu with reset color scale action.
        Middle mouse click resets the axis with the settings in the config tree.
    """
    # Use a QueuedConnection to connect to sigResetColorScale so that the reset is scheduled after
    # all current events have been processed. Otherwise the mouseReleaseEvent may look for a
    # PlotCurveItem that is no longer present after the reset, which results in a RuntimeError:
    # wrapped C/C++ object of type PlotCurveItem has been deleted.
    sigResetColorScale = QtSignal()  # Signal the inspectors to reset the color scale


    def __init__(self, *args, histHeightPercentile=99.0, **kwargs):
        """ Constructor
        """
        super(ArgosColorLegendItem, self).__init__(
            *args, histHeightPercentile=histHeightPercentile, **kwargs)
        self.resetColorScaleAction = QtWidgets.QAction("Reset Color Range", self)
        self.resetColorScaleAction.triggered.connect(self.emitResetColorScaleSignal)
        self.resetColorScaleAction.setToolTip("Reset the range of the color scale.")
        self.addAction(self.resetColorScaleAction)


    @classmethod
    def _imageItemHasIntegerData(cls, imageItem):
        """ Returns True if the imageItem contains integer data.

            Overriden so that the ImagePlotItem can replace integer arrays with float arrays (to
            plot masked values as NaNs) while it still calculates the histogram bins as if it
            where integers (to prevent aliasing)
        """
        check_class(imageItem, pg.ImageItem, allow_none=True)

        if hasattr(imageItem, '_wasIntegerData'):
            return imageItem._wasIntegerData
        else:
            return super(ArgosColorLegendItem, cls)._imageItemHasIntegerData(imageItem)


    def emitResetColorScaleSignal(self):
        """ Emits the sigColorScaleReset to request the inspectors to reset the color scale
        """
        logger.debug("Emitting sigColorScaleReset() for {!r}".format(self))
        self.sigResetColorScale.emit()


    def mouseClickEvent(self, mouseClickEvent):
        """ Handles (PyQtGraph) mouse click events.

            Overrides the middle mouse click to reset using the settings in the config tree.

            Opens the context menu if a right mouse button was clicked. (We can't simply use
            setContextMenuPolicy(Qt.ActionsContextMenu because the PlotItem class does not derive
            from QWidget).

            :param mouseClickEvent: pyqtgraph.GraphicsScene.mouseEvents.MouseClickEvent
        """
        if mouseClickEvent.button() in self.resetRangeMouseButtons:
            self.emitResetColorScaleSignal()
            mouseClickEvent.accept()

        elif mouseClickEvent.button() == QtCore.Qt.RightButton:
            contextMenu = QtWidgets.QMenu()
            for action in self.actions():
                contextMenu.addAction(action)

            screenPos = mouseClickEvent.screenPos() # Screenpos is a QPointF, convert to QPoint.
            screenX = round(screenPos.x())
            screenY = round(screenPos.y())
            contextMenu.exec_(QtCore.QPoint(screenX, screenY))

        else:
            super(ArgosColorLegendItem, self).mouseClickEvent(mouseClickEvent)

