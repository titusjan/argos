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

""" Configuration Tree Items for use in PyQtGraph-based inspectors
"""
from __future__ import division, print_function

import logging

from libargos.config.groupcti import GroupCti
from libargos.config.boolcti import BoolCti
from libargos.config.floatcti import FloatCti
from libargos.config.untypedcti import UntypedCti
from libargos.info import DEBUGGING

logger = logging.getLogger(__name__)



class ViewBoxDebugCti(GroupCti):
    """ Read-only config tree for inspecting a PyQtGraph ViewBox
    """
    def __init__(self, nodeName, expanded=True):

        # TODO: should configs have a link back to an inspector?
        super(ViewBoxDebugCti, self).__init__(nodeName, defaultData=None, expanded=expanded)

        self.insertChild(UntypedCti("targetRange", [[0,1], [0,1]],
            doc="Child coord. range visible [[xmin, xmax], [ymin, ymax]]"))

        self.insertChild(UntypedCti("viewRange", [[0,1], [0,1]],
            doc="Actual range viewed"))

        self.insertChild(UntypedCti("xInverted", None))
        self.insertChild(UntypedCti("yInverted", None))
        self.insertChild(UntypedCti("aspectLocked", False,
            doc="False if aspect is unlocked, otherwise float specifies the locked ratio."))
        self.insertChild(UntypedCti("autoRange", [True, True],
            doc="False if auto range is disabled, otherwise float gives the fraction of data that is visible"))
        self.insertChild(UntypedCti("autoPan", [False, False],
            doc="Whether to only pan (do not change scaling) when auto-range is enabled"))
        self.insertChild(UntypedCti("autoVisibleOnly", [False, False],
            doc="Whether to auto-range only to the visible portion of a plot"))
        self.insertChild(UntypedCti("linkedViews", [None, None],
            doc="may be None, 'viewName', or weakref.ref(view) a name string indicates that the view *should* link to another, but no view with that name exists yet."))
        self.insertChild(UntypedCti("mouseEnabled", [None, None]))
        self.insertChild(UntypedCti("mouseMode", None))
        self.insertChild(UntypedCti("enableMenu", None))
        self.insertChild(UntypedCti("wheelScaleFactor", None))
        self.insertChild(UntypedCti("background", None))

        self.limitsItem = self.insertChild(GroupCti("limits"))
        self.limitsItem.insertChild(UntypedCti("xLimits", [None, None],
            doc="Maximum and minimum visible X values "))
        self.limitsItem.insertChild(UntypedCti("yLimits", [None, None],
            doc="Maximum and minimum visible Y values"))
        self.limitsItem.insertChild(UntypedCti("xRange", [None, None],
            doc="Maximum and minimum X range"))
        self.limitsItem.insertChild(UntypedCti("yRange", [None, None],
            doc="Maximum and minimum Y range"))


    def viewBoxChanged(self, viewBox):
        """ Updates the config settings
        """
        for key, value in viewBox.state.items():
            if key != "limits":
                childItem = self.childByNodeName(key)
                childItem.data = value
            else:
                # limits contains a dictionary as well
                for limitKey, limitValue in value.items():
                    limitChildItem = self.limitsItem.childByNodeName(limitKey)
                    limitChildItem.data = limitValue



class PgAxisCti(GroupCti):
    """ Configuration tree for a plot axis
    """
    def __init__(self, nodeName, defaultData=None, axisNumber=None):
        """ Constructor
        """
        super(PgAxisCti, self).__init__(nodeName, defaultData=defaultData)

        assert axisNumber in (0, 1), "axisName must be 0 or 1"
        self._axisNumber = axisNumber

        #self.insertChild(BoolCti("show", True)) # TODO:
        self.insertChild(BoolCti('logarithmic', False))

        # Keep a reference because this needs to be changed often/fast
        self.rangeItem = self.insertChild(GroupCti('range'))
        self.rangeMinItem = self.rangeItem.insertChild(FloatCti('min', 0.0))
        self.rangeMaxItem = self.rangeItem.insertChild(FloatCti('max', 0.0))

        self.autoRangeItem = self.rangeItem.insertChild(BoolCti("auto-range", True))


    def getRange(self):
        "Returns a tuple with the min and max range"
        return (self.rangeMinItem.data, self.rangeMaxItem.data)


    def viewBoxChanged(self, viewBox):
        """ Called when the range of the axis is changed. Updates the range in the config tree.
        """
        #self.rangeMinItem.data, self.rangeMaxItem.data = newRange
        #self.autoRangeItem.data = bool(viewBox.autoRangeEnabled()[self._axisNumber])
        #self.model.emitDataChanged(self.rangeItem)

        state = viewBox.state
        autoRangeEnabled = bool(viewBox.autoRangeEnabled()[self._axisNumber])

        self.rangeMinItem.data, self.rangeMaxItem.data = state['viewRange'][self._axisNumber]
        self.rangeMinItem.enabled = not autoRangeEnabled
        self.rangeMaxItem.enabled = not autoRangeEnabled
        self.autoRangeItem.data = autoRangeEnabled

        self.model.emitDataChanged(self.rangeItem)




class ViewBoxCti(GroupCti):
    """ Read-only config tree for inspecting a PyQtGraph ViewBox
    """
    def __init__(self, nodeName='axes'):

        super(ViewBoxCti, self).__init__(nodeName, defaultData=None)

        self._updatingViewBox = False #

        # Axes (keeping references to the axis CTIs because they need to be updated quickly when
        # the range changes; self.configValue may be slow.)
        self.aspectItem = self.insertChild(BoolCti("lock aspect ratio", False))
        self.xAxisItem = self.insertChild(PgAxisCti('X-axis', axisNumber=0))
        self.yAxisItem = self.insertChild(PgAxisCti('Y-axis', axisNumber=1))

        if DEBUGGING:
            self.stateItem = self.insertChild(ViewBoxDebugCti('state', expanded=False))
        else:
            self.stateItem = None


    def viewBoxChanged(self, viewBox):
        """ Called when the x-range of the plot is changed. Updates the values in the config tree.

            Is disabled during execution of updateViewBox so it doesn't prematurely update the
            config tree item settings.
        """
        if self._updatingViewBox:
            #logger.debug("viewBoxChanged: ignored")
            return

        #logger.debug("viewBoxChanged: {}".format(viewBox.autoRangeEnabled()))

        self.xAxisItem.viewBoxChanged(viewBox)
        self.yAxisItem.viewBoxChanged(viewBox)

        if self.stateItem:
            self.stateItem.viewBoxChanged(viewBox)



    def updateViewBox(self, viewBox):
        """ Updates the viewBox from the configuration values.
            Returns the viewBox
        """
        self._updatingViewBox = True # defer calling self.viewBoxChanged
        try:
            viewBox.setAspectLocked(self.aspectItem.configValue)
            # TODO: show axis/label

            autoRangeX = self.xAxisItem.autoRangeItem.data
            if autoRangeX:
                #logger.debug("enableAutoRange: {}, {}".format(viewBox.XAxis, autoRangeX))
                viewBox.enableAutoRange(viewBox.XAxis, autoRangeX)
            else:
                #logger.debug("Setting xRange: {}".format(self.xAxisItem.getRange()))
                viewBox.setRange(xRange = self.xAxisItem.getRange(),
                                 padding=0, update=False, disableAutoRange=True)

            autoRangeY = self.yAxisItem.autoRangeItem.data
            if autoRangeY:
                #logger.debug("enableAutoRange: {}, {}".format(viewBox.YAxis, autoRangeY))
                viewBox.enableAutoRange(viewBox.YAxis, autoRangeY)
            else:
                #logger.debug("Setting yRange: {}".format(self.yAxisItem.getRange()))
                viewBox.setRange(yRange = self.yAxisItem.getRange(),
                                 padding=0, update=False, disableAutoRange=True)
        finally:
            self._updatingViewBox = False

        self.viewBoxChanged(viewBox)
        return viewBox
