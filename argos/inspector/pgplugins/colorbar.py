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

from argos.utils.cls import check_class
from pgcolorbar.colorlegend import ColorLegendItem

# from argos.info import DEBUGGING
# from argos.qt import Qt, QtCore, QtWidgets, QtSignal

logger = logging.getLogger(__name__)


class ArgosColorLegendItem(ColorLegendItem):
    """ Wrapper around pgcolorbar.colorlegend.ColorLegendItem.

        Supresses the FutureWarning of PyQtGraph in
        Overrides the _imageItemHasIntegerData method.
        Middle mouse click resets the axis.
    """

    @classmethod
    def _imageItemHasIntegerData(cls, imageItem):
        """ Returns True if the imageItem contains integer data.

            Overriden so that the ImagePlotItem can replace integer arrays with float arrays (to
            plot masked values as NaNs) while it still calculates the histogram bins as if it
            where integers (tp prevent aliasing)
        """
        check_class(imageItem, pg.ImageItem, allow_none=True)

        if hasattr(imageItem, '_wasIntegerData'):
            return imageItem._wasIntegerData
        else:
            return super()._imageItemHasIntegerData(imageItem)


    def _updateHistogram(self):
        """ Updates the histogram with data from the image.

            Suppresses the numpy future warning in PyQtGraph.
        """
        with warnings.catch_warnings():
            warnings.simplefilter(action='ignore', category=FutureWarning)
            super()._updateHistogram()
