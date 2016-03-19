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
from libargos.config.choicecti import ChoiceCti
from libargos.config.floatcti import FloatCti
from libargos.config.untypedcti import UntypedCti
from libargos.info import DEBUGGING
from libargos.utils.cls import check_class

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
    """ Configuration tree item for a PyQtGraph plot axis.

        This CTI is intended to be used as a child of a PgPlotItemCti.
    """
    def __init__(self, nodeName, defaultData=None, axisNumber=None):
        """ Constructor
        """
        super(PgAxisCti, self).__init__(nodeName, defaultData=defaultData)

        self.axisNumber = axisNumber

        #self.insertChild(BoolCti("show", True)) # TODO:
        self.insertChild(BoolCti('logarithmic', False))

        # Keep a reference because this needs to be changed often/fast
        self.rangeItem = self.insertChild(GroupCti('range'))
        self.rangeMinItem = self.rangeItem.insertChild(FloatCti('min', 0.0))
        self.rangeMaxItem = self.rangeItem.insertChild(FloatCti('max', 0.0))

        self.autoRangeItem = self.rangeItem.insertChild(BoolCti("auto-range", True))


    def getRange(self):
        """Returns a tuple with the min and max range
        """
        return (self.rangeMinItem.data, self.rangeMaxItem.data)


    def viewBoxChanged(self, viewBox):
        """ Called when the range of the axis is changed. Updates the range in the config tree.
        """
        #self.rangeMinItem.data, self.rangeMaxItem.data = newRange
        #self.autoRangeItem.data = bool(viewBox.autoRangeEnabled()[self._axisNumber])
        #self.model.emitDataChanged(self.rangeItem)

        state = viewBox.state
        axisNumber = self.axisNumber
        assert axisNumber in (0, 1), "axisName must be 0 or 1"

        autoRangeEnabled = bool(viewBox.autoRangeEnabled()[axisNumber])

        self.rangeMinItem.data, self.rangeMaxItem.data = state['viewRange'][axisNumber]
        self.rangeMinItem.enabled = not autoRangeEnabled
        self.rangeMaxItem.enabled = not autoRangeEnabled
        self.autoRangeItem.data = autoRangeEnabled

        self.model.emitDataChanged(self.rangeItem)



class PgIndependendAxisCti(PgAxisCti):
    """ Configuration tree item for a plot axis showing an independend variable
    """
    def __init__(self, nodeName, defaultData=None, axisNumber=None, axisName=None):
        """ Constructor
        """
        super(PgIndependendAxisCti, self).__init__(nodeName, defaultData=defaultData,
                                                   axisNumber=axisNumber)
        self.axisName = axisName
        self.insertChild(ChoiceCti('label', 0, editable=True,
                                   configValues=["{{{}-dim}}".format(axisName)]),
                         position=0)


class PgDependendAxisCti(PgAxisCti):
    """ Configuration tree item for a plot axis showing a dependend variable
    """
    def __init__(self, nodeName, defaultData=None, axisNumber=None, axisName=None):
        """ Constructor
        """
        super(PgDependendAxisCti, self).__init__(nodeName, defaultData=defaultData,
                                                 axisNumber=axisNumber)
        self.axisName = axisName
        self.insertChild(ChoiceCti('label', 1, editable=True,
                                   configValues=["{name}", "{name} {unit}",
                                                 "{path}", "{path} {unit}"]),
                         position=0)




class PgPlotItemCti(GroupCti):
    """ Config tree item for manipulating a PyQtGraph.PlotItem
    """
    def __init__(self, nodeName='axes', plotItem=None,
                 xAxisCti=None, yAxisCti=None):
        """ Constructor
        """
        super(PgPlotItemCti, self).__init__(nodeName, defaultData=None)

        #check_class(plotItem, (PlotItem, SimplePlotItem) # TODO
        assert plotItem, "target plotItem is undefined"
        self.plotItem = plotItem
        self._applyInProgress = False
        self.aspectItem = self.insertChild(BoolCti("lock aspect ratio", False))

        # Keeping references to the axes CTIs because they need to be updated quickly when
        # the range changes; getting by path may be slow.)
        if xAxisCti is None:
            self.xAxisCti = self.insertChild(PgAxisCti('x-axis', axisNumber=0))
        else:
            check_class(xAxisCti, PgAxisCti)
            self.xAxisCti = self.insertChild(xAxisCti)

        if yAxisCti is None:
            self.yAxisCti = self.insertChild(PgAxisCti('y-axis', axisNumber=1))
        else:
            check_class(yAxisCti, PgAxisCti)
            self.yAxisCti = self.insertChild(yAxisCti)

        if DEBUGGING:
            self.stateItem = self.insertChild(ViewBoxDebugCti('state', expanded=False))
        else:
            self.stateItem = None

        # Connect signals
        viewBox = self.plotItem.getViewBox()
        viewBox.sigStateChanged.connect(self.viewBoxChanged)


    def _closeResources(self):
        """ Disconnects signals.
            Is called by self.finalize when the cti is deleted.
        """
        viewBox = self.plotItem.getViewBox()
        viewBox.sigStateChanged.disconnect(self.viewBoxChanged)


    def viewBoxChanged(self, viewBox):
        """ Called when the range of the plot is changed. Refreshes the values in the config tree.

            Is disabled during execution of apply so it doesn't prematurely refresh the
            config tree item settings.
        """
        if self._applyInProgress:
            #logger.debug("viewBoxChanged: ignored")
            return

        #logger.debug("viewBoxChanged: {}".format(viewBox.autoRangeEnabled()))

        self.xAxisCti.viewBoxChanged(viewBox)
        self.yAxisCti.viewBoxChanged(viewBox)

        if self.stateItem:
            self.stateItem.viewBoxChanged(viewBox)


    def apply(self):
        """ Applies the configuration to the target PlotItem it monitors.
        """
        self._applyInProgress = True # defer calling self.viewBoxChanged
        try:
            viewBox = self.plotItem.getViewBox()
            viewBox.setAspectLocked(self.aspectItem.configValue)
            # TODO: show axis/label

            autoRangeX = self.xAxisCti.autoRangeItem.data
            if autoRangeX:
                #logger.debug("enableAutoRange: {}, {}".format(viewBox.XAxis, autoRangeX))
                viewBox.enableAutoRange(viewBox.XAxis, autoRangeX)
            else:
                #logger.debug("Setting xRange: {}".format(self.xAxisItem.getRange()))
                viewBox.setRange(xRange = self.xAxisCti.getRange(),
                                 padding=0, update=False, disableAutoRange=True)

            autoRangeY = self.yAxisCti.autoRangeItem.data
            if autoRangeY:
                #logger.debug("enableAutoRange: {}, {}".format(viewBox.YAxis, autoRangeY))
                viewBox.enableAutoRange(viewBox.YAxis, autoRangeY)
            else:
                #logger.debug("Setting yRange: {}".format(self.yAxisItem.getRange()))
                viewBox.setRange(yRange = self.yAxisCti.getRange(),
                                 padding=0, update=False, disableAutoRange=True)
        finally:
            self._applyInProgress = False

        # Call viewBoxChanged in case the newly applied configuration resulted in a change of the
        # viewbox state.
        self.viewBoxChanged(viewBox)

