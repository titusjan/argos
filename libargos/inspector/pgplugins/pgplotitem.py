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

logger = logging.getLogger(__name__)

USE_SIMPLE_PLOT = False

if USE_SIMPLE_PLOT:
    # An experimental simplification of PlotItem. Not included in the distribution
    logger.warn("Using SimplePlotItem as PlotItem")
    from pyqtgraph.graphicsItems.PlotItem.simpleplotitem import SimplePlotItem
else:
    from pyqtgraph.graphicsItems.PlotItem import PlotItem as SimplePlotItem



class ArgosPgPlotItem(SimplePlotItem):
    """ Wrapper arround pyqtgraph.graphicsItems.PlotItem
        Overrides the autoBtnClicked method.
    """
    def autoBtnClicked(self):
        """ Hides the button but does not enable/disable autorange.
            That will be done by PgAxisRangeCti
        """
        logger.debug("ArgosPgPlotItem.autoBtnClicked, mode:{}".format(self.autoBtn.mode))
        if self.autoBtn.mode == 'auto':
            #self.enableAutoRange()
            self.autoBtn.hide()
        else:
            pass
            #self.disableAutoRange()

