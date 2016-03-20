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

        super(ViewBoxDebugCti, self).__init__(nodeName, expanded=expanded)

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



# class PgViewBoxCtiMixin():
#     """ Mixin that adds two emtpy methods that are called by PgPlotItem on all its child items.
#
#         The methods are refresh
#     """


class PgAxisAutoRangeCti(GroupCti):
    """ Configuration tree item is linked to the axis range.
        Can toggle the axis' auto-range property on/off by means of checkbox
    """
    def __init__(self, viewBox, axisNumber, nodeName='range'):
        """ Constructor.
            The monitored axis is specified by viewBox and axisNumber (0 for x-axis, 1 for y-axis)
        """
        super(PgAxisAutoRangeCti, self).__init__(nodeName)
        assert axisNumber in (0, 1), "axisNumber must be 0 or 1"
        self.viewBox = viewBox
        self.axisNumber = axisNumber

        self.rangeMinItem = self.insertChild(FloatCti('min', 0.0))
        self.rangeMaxItem = self.insertChild(FloatCti('max', 0.0))
        self.autoRangeItem = self.insertChild(BoolCti("auto-range", True))


    def refresh(self):
        """ Refreshes the config values from the axes' state
        """
        self.rangeMinItem.data, self.rangeMaxItem.data = \
            self.viewBox.state['viewRange'][self.axisNumber]
        autoRangeEnabled = bool(self.viewBox.autoRangeEnabled()[self.axisNumber])
        self.rangeMinItem.enabled = not autoRangeEnabled
        self.rangeMaxItem.enabled = not autoRangeEnabled
        self.autoRangeItem.data = autoRangeEnabled

        self.model.emitDataChanged(self)


    def getRange(self):
        """Returns a tuple with the min and max range
        """
        return (self.rangeMinItem.data, self.rangeMaxItem.data)


    def apply(self):
        """ Applies the configuration to the target axis it monitors.
        """
        autoRange = self.autoRangeItem.configValue

        if autoRange:
            #logger.debug("enableAutoRange: {}, {}".format(viewBox.XAxis, autoRangeX))
            self.viewBox.enableAutoRange(self.axisNumber, autoRange)
        else:
            if self.axisNumber == self.viewBox.XAxis:
                xRange, yRange = self.getRange(), None
            else:
                xRange, yRange = None, self.getRange()

            # viewBox.setRange doesn't accept an axis number :-(
            self.viewBox.setRange(xRange = xRange, yRange=yRange,
                                  padding=0, update=False, disableAutoRange=True)



class PgAxisCti(GroupCti):
    """ Configuration tree item for a PyQtGraph plot axis.

        This CTI is intended to be used as a child of a PgPlotItemCti.
    """
    def __init__(self, nodeName, viewBox, axisNumber):
        """ Constructor
        """
        super(PgAxisCti, self).__init__(nodeName)

        assert axisNumber in (0, 1), "axisNumber must be 0 or 1"
        self.viewBox = viewBox
        self.axisNumber = axisNumber

        #self.insertChild(BoolCti("show", True)) # TODO:
        self.insertChild(BoolCti('logarithmic', False))

        self.rangeItem = self.insertChild(PgAxisAutoRangeCti(self.viewBox, self.axisNumber))


    def refresh(self):
        """ Called when the range of the axis is changed. Updates the range in the config tree.
        """
        self.rangeItem.refresh()


    def apply(self):
        """ Applies the configuration to the target axis it monitors.
        """
        self.rangeItem.apply()



class PgIndependendAxisCti(PgAxisCti):
    """ Configuration tree item for a plot axis showing an independend variable
    """
    def __init__(self, nodeName, viewBox, axisNumber, axisName):
        """ Constructor
        """
        super(PgIndependendAxisCti, self).__init__(nodeName, viewBox, axisNumber)
        self.axisName = axisName
        labelCti = ChoiceCti('label', 0, editable=True,
                             configValues=["{{{}-dim}}".format(axisName)])
        self.insertChild(labelCti, position=0)


class PgDependendAxisCti(PgAxisCti):
    """ Configuration tree item for a plot axis showing a dependend variable
    """
    def __init__(self, nodeName, viewBox, axisNumber, axisName):
        """ Constructor
        """
        super(PgDependendAxisCti, self).__init__(nodeName, viewBox, axisNumber)
        self.axisName = axisName
        labelCti = ChoiceCti('label', 1, editable=True,
                             configValues=["{name}", "{name} {unit}", "{path}", "{path} {unit}"])
        self.insertChild(labelCti, position=0)



class PgPlotItemCti(GroupCti):
    """ Config tree item for manipulating a PyQtGraph.PlotItem
    """
    def __init__(self, nodeName='axes', plotItem=None, xAxisCti=None, yAxisCti=None):
        """ Constructor
        """
        super(PgPlotItemCti, self).__init__(nodeName)

        #check_class(plotItem, (PlotItem, SimplePlotItem) # TODO
        assert plotItem, "target plotItem is undefined"
        self._applyInProgress = False
        self.aspectItem = self.insertChild(BoolCti("lock aspect ratio", False))
        self.plotItem = plotItem
        viewBox = plotItem.getViewBox()

        # Keeping references to the axes CTIs because they need to be updated quickly when
        # the range changes; getting by path may be slow.)
        if xAxisCti is None:
            self.xAxisCti = self.insertChild(PgAxisCti('x-axis', viewBox, 0))
        else:
            check_class(xAxisCti, PgAxisCti)
            self.xAxisCti = self.insertChild(xAxisCti)

        if yAxisCti is None:
            self.yAxisCti = self.insertChild(PgAxisCti('y-axis', viewBox, 1))
        else:
            check_class(yAxisCti, PgAxisCti)
            self.yAxisCti = self.insertChild(yAxisCti)

        if DEBUGGING:
            self.stateItem = self.insertChild(ViewBoxDebugCti('viewbox state', expanded=False))
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
            return

        self.xAxisCti.refresh()
        self.yAxisCti.refresh()

        if self.stateItem:
            self.stateItem.viewBoxChanged(viewBox)


    def apply(self):
        """ Applies the configuration to the target PlotItem it monitors.
        """
        self._applyInProgress = True # defer calling self.viewBoxChanged
        try:
            viewBox = self.plotItem.getViewBox()
            viewBox.setAspectLocked(self.aspectItem.configValue)

            self.xAxisCti.apply()
            self.yAxisCti.apply()
        finally:
            self._applyInProgress = False

        # Call viewBoxChanged in case the newly applied configuration resulted in a change of the
        # viewbox state.
        self.viewBoxChanged(viewBox)

