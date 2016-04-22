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
import numpy as np
import pyqtgraph as pg

from collections import OrderedDict
from libargos.config.groupcti import GroupCti
from libargos.config.boolcti import BoolCti
from libargos.config.choicecti import ChoiceCti
from libargos.config.intcti import IntCti
from libargos.config.floatcti import SnFloatCti, FloatCti
from libargos.config.untypedcti import UntypedCti
from libargos.info import DEBUGGING
from libargos.utils.cls import check_class

logger = logging.getLogger(__name__)

X_AXIS = pg.ViewBox.XAxis
Y_AXIS = pg.ViewBox.YAxis
VALID_AXIS_POSITIONS =  ('left', 'right', 'bottom', 'top')



# Python closures are late-binding
# http://docs.python-guide.org/en/latest/writing/gotchas/#late-binding-closures
def makePyQtAutoRangeFn(viewBox, axisNumber):
    """ Generates a function that calculates the range of an axis of a PyQtGraph ViewBox.
    """
    assert axisNumber in (X_AXIS, Y_AXIS), "axisNumber must be 0 or 1"

    def calcRange():
        """ Calculates the range from the sliced array. Discards percentage of the minimum and
            percentage of the maximum values of the inspector.slicedArray
        """
        rect = viewBox.childrenBoundingRect() # taken from viewBox.autoRange()
        if rect is not None:
            if axisNumber == X_AXIS:
                return rect.left(), rect.right()
            else:
                return rect.bottom(), rect.top()
        else:
            # Does this happen? Probably when the plot is empty.
            raise AssertionError("No children bbox. Plot range not updated.")

    return calcRange


class ViewBoxDebugCti(GroupCti):
    """ Read-only config tree for inspecting a PyQtGraph ViewBox
    """
    def __init__(self, nodeName, viewBox, expanded=False):

        super(ViewBoxDebugCti, self).__init__(nodeName, expanded=expanded)

        self.viewBox = viewBox

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


    def _refreshNodeFromTarget(self):
        """ Updates the config settings
        """
        for key, value in self.viewBox.state.items():
            if key != "limits":
                childItem = self.childByNodeName(key)
                childItem.data = value
            else:
                # limits contains a dictionary as well
                for limitKey, limitValue in value.items():
                    limitChildItem = self.limitsItem.childByNodeName(limitKey)
                    limitChildItem.data = limitValue


# Python closures are late-binding
# http://docs.python-guide.org/en/latest/writing/gotchas/#late-binding-closures
def makeInspectorPercentileRangeFn(inspector, percentage):
    """ Generates a function that calculates the range of the sliced array of the inspector
        by discarding a percentage of the outliers (at both ends, minimum and maximum)

        The first parameter is an inspector, and not an array, because we would then have to
        regenerate ther range function every time sliced array of an inspector changes.
    """
    assert hasattr(inspector, "slicedArray"), "The inspector must have a 'slicedArray' attribute."

    def calcRange():
        """ Calculates the range from the sliced array. Discards percentage of the minimum and
            percentage of the maximum values of the inspector.slicedArray
        """
        array = inspector.slicedArray
        logger.debug("Discarding {}% from id: {}".format(percentage, id(array)))
        return np.nanpercentile(array, (percentage, 100-percentage) )

    return calcRange


def defaultAutoRangeMethods(inspector, intialItems=None):
    """ Creates an ordered dict with default autorange methods for an inspector.

        :param inspector: the range methods will work on (the sliced array) of this inspector.
        :param intialItems: will be passed on to the  OrderedDict constructor.
    """
    rangeFunctions = OrderedDict({} if intialItems is None else intialItems)
    rangeFunctions['use all data'] = makeInspectorPercentileRangeFn(inspector, 0.0)
    for percentage in [0.1, 0.2, 0.5, 1, 2, 5, 10, 20]:
        label = "discard {}%".format(percentage)
        rangeFunctions[label] = makeInspectorPercentileRangeFn(inspector, percentage)
    return rangeFunctions


class AbstractRangeCti(GroupCti):
    """ Configuration tree item is linked to a target range.

        Is an abstract class. Descendants must override getTargetRange and setTargetRange
    """
    def __init__(self, autoRangeFunctions=None, nodeName='range'):
        """ Constructor.
            The target axis is specified by viewBox and axisNumber (0 for x-axis, 1 for y-axis)

            If given, autoRangeMethods must be a (label to function) dictionary that will be used
            to populate the (auto range) method ChoiceCti.
            If autoRangeMethods is None, there will be no auto-range child CTI.
            If autoRangeMethods has one element there will be an auto-range child without a method
            child CTI (the function from the autoRangeMethods dictionary will be the default).
        """
        super(AbstractRangeCti, self).__init__(nodeName)

        self.rangeMinCti = self.insertChild(SnFloatCti('min', 0.0))
        self.rangeMaxCti = self.insertChild(SnFloatCti('max', 1.0))

        self._rangeFunctions = {}
        self.autoRangeCti = None
        self.methodCti = None
        self.paddingCti = None

        if autoRangeFunctions is not None:
            self.autoRangeCti = self.insertChild(BoolCti("auto-range", True))
            self._rangeFunctions = autoRangeFunctions

            if len(autoRangeFunctions) > 1:
                self.methodCti = ChoiceCti("method", configValues=autoRangeFunctions.keys())
                self.autoRangeCti.insertChild(self.methodCti)

            self.paddingCti = IntCti("padding", -1, suffix="%", specialValueText="dynamic",
                                     minValue=-1, maxValue=1000, stepSize=1)
            self.autoRangeCti.insertChild(self.paddingCti)


    @property
    def autoRangeMethod(self):
        """ The currently selected auto range method.
            If there is no method child CTI there will be only one method, which will be returened.
        """
        if self.methodCti:
            return self.methodCti.configValue
        else:
            assert len(self._rangeFunctions) == 1, \
                "Assumed only one _rangeFunctions. Got: {}".format(self._rangeFunctions)
            return self._rangeFunctions.keys()[0]


    def _refreshNodeFromTarget(self, *args, **kwargs):
        """ Refreshes the configuration from the target it monitors (if present).
            The default implementation does nothing; subclasses can override it.
            During updateTarget's execution refreshFromTarget is blocked to avoid loops.

            The *args and **kwargs arguments are ignored but make it possible to use this as a slot
            for signals with arguments.
        """
        self._refreshAutoRange()
        self._refreshMinMax(self.getTargetRange())


    def _refreshMinMax(self, axisRange):
        """ Refreshes the min max config values from the axes' state.

            ranges = [[xmin, xmax], [ymin, ymax]]
        """
        # Set the precision from by looking how many decimals are neede to show the difference
        # between the minimum and maximum, given the maximum. E.g. if min = 0.04 and max = 0.07,
        # we would only need zero decimals behind the point as we can write the range as
        # [4e-2, 7e-2]. However if min = 1.04 and max = 1.07, we need 2 decimals behind the point.
        # So while the range is the same size, we need more decimals because we are not zoomed in
        # around zero.
        rangeMin, rangeMax = axisRange
        maxOrder = int(np.log10(np.abs(max(rangeMax, rangeMin))))
        diffOrder = int(np.log10(np.abs(rangeMax - rangeMin)))

        extraDigits = 2 # add some extra digits to make each pan/zoom action show a new value.
        precision = min(25, max(extraDigits + 1, abs(maxOrder - diffOrder) + extraDigits)) # clip
        #logger.debug("maxOrder: {}, diffOrder: {}, precision: {}"
        #             .format(maxOrder, diffOrder, precision))

        self.rangeMinCti.precision = precision
        self.rangeMaxCti.precision = precision
        self.rangeMinCti.data, self.rangeMaxCti.data = rangeMin, rangeMax

        # Update values in the tree
        self.model.emitDataChanged(self.rangeMinCti)
        self.model.emitDataChanged(self.rangeMaxCti)


    def _refreshAutoRange(self):
        """ The min and max config items will be disabled if auto range is on.
        """
        enabled = self.autoRangeCti and self.autoRangeCti.configValue

        self.rangeMinCti.enabled = not enabled
        self.rangeMaxCti.enabled = not enabled
        self.model.emitDataChanged(self)


    def _setAutoRangeOn(self):
        """ Not implemented for single axis. See PgPlotItemCti._setAutorangeOn
        """
        assert False, "Not implemented for single axis. See PgPlotItemCti._setAutorangeOn"


    def _setAutoRangeOff(self):
        """ Turns off the auto range checkbox.
            Calls _refreshNodeFromTarget, not _updateTargetFromNode because setting auto range off
            does not require a redraw of the target.
        """
        if self.autoRangeCti:
            self.autoRangeCti.data = False
        self._refreshNodeFromTarget()


    def calculateRange(self):
        """ Calculates the range depending on the config settings.
        """
        if not self.autoRangeCti or not self.autoRangeCti.configValue:
            return (self.rangeMinCti.data, self.rangeMaxCti.data)
        else:
            rangeFunction = self._rangeFunctions[self.autoRangeMethod]
            return rangeFunction()


    def _updateTargetFromNode(self):
        """ Applies the configuration to the target axis.
        """
        if not self.autoRangeCti or not self.autoRangeCti.configValue:
            padding = 0
        elif self.paddingCti.configValue == -1: # specialValueText
            # PyQtGraph dynamice padding: between 0.02 and 0.1 dep. on the size of the ViewBox
            padding = None
        else:
            padding = self.paddingCti.configValue / 100

        targetRange = self.calculateRange()
        #logger.debug("axisRange: {}, padding={}".format(targetRange, padding))
        if not np.all(np.isfinite(targetRange)):
            logger.warn("New target range is not finite. Plot range not updated")
            return

        self.setTargetRange(targetRange, padding=padding)


    def getTargetRange(self):
        """ Gets the range of the target
        """
        raise NotImplementedError("Abstract method. Please override.")


    def setTargetRange(self, targetRange, padding=None):
        """ Sets the range of the target.
        """
        # The padding parameter is a bit of a hack. TODO: better?
        raise NotImplementedError("Abstract method. Please override.")



class PgHistLutRangeCti(AbstractRangeCti):
    """ Configuration tree item is linked to the HistogramLUTItem range.
    """
    def __init__(self, histLutItem, autoRangeFunctions=None, nodeName='color range'):
        """ Constructor.
            The target axis is specified by viewBox and axisNumber (0 for x-axis, 1 for y-axis)

            If given, autoRangeFunctions must be a (label to function) dictionary that will be used
            to populate the (auto range) method ChoiceCti. If not give, the there will not be
            a method choice and the autorange implemented by PyQtGraph will be used.
        """
        super(PgHistLutRangeCti, self).__init__(autoRangeFunctions=autoRangeFunctions,
                                                nodeName=nodeName)
        check_class(histLutItem, pg.HistogramLUTItem)
        self.histLutItem = histLutItem

        # Connect signals
        #  sigLevelChangeFinished is triggered only at the end of a drag
        self.histLutItem.sigLevelsChanged.connect(self._setAutoRangeOff)
        #self.histLutItem.sigLevelChangeFinished.connect(self._setAutoRangeOff)


    def _closeResources(self):
        """ Disconnects signals.
            Is called by self.finalize when the cti is deleted.
        """
        self.histLutItem.sigLevelsChanged.connect(self._setAutoRangeOff)
        #self.histLutItem.sigLevelChangeFinished.disconnect(self._setAutoRangeOff)


    def getTargetRange(self):
        """ Gets the range of the target
        """
        return self.histLutItem.getLevels()


    def setTargetRange(self, targetRange, padding=None):
        """ Sets the range of the target.
        """
        rangeMin, rangeMax = targetRange
        self.histLutItem.setLevels(rangeMin, rangeMax)



class PgAxisRangeCti(AbstractRangeCti):
    """ Configuration tree item is linked to the axis range.
    """
    PYQT_RANGE = 'by PyQtGraph'

    def __init__(self, viewBox, axisNumber, autoRangeFunctions=None, nodeName='range'):
        """ Constructor.
            The target axis is specified by viewBox and axisNumber (0 for x-axis, 1 for y-axis)

            If given, autoRangeFunctions must be a (label to function) dictionary that will be used
            to populate the (auto range) method ChoiceCti. If not give, the there will not be
            a method choice and the autorange implemented by PyQtGraph will be used.
        """
        if autoRangeFunctions is None:
            autoRangeFunctions = {self.PYQT_RANGE: makePyQtAutoRangeFn(viewBox, axisNumber)}

        super(PgAxisRangeCti, self).__init__(autoRangeFunctions=autoRangeFunctions, nodeName=nodeName)
        check_class(viewBox, pg.ViewBox)
        assert axisNumber in (X_AXIS, Y_AXIS), "axisNumber must be 0 or 1"

        self.viewBox = viewBox
        self.axisNumber = axisNumber

        if DEBUGGING:
            self.insertChild(ViewBoxDebugCti('viewbox state', self.viewBox))


        # Connect signals
        self.viewBox.sigRangeChangedManually.connect(self._setAutoRangeOff)


    def _closeResources(self):
        """ Disconnects signals.
            Is called by self.finalize when the cti is deleted.
        """
        self.viewBox.sigRangeChangedManually.disconnect(self._setAutoRangeOff)


    def getTargetRange(self):
        """ Gets the range of the target
        """
        return self.viewBox.state['viewRange'][self.axisNumber]


    def setTargetRange(self, targetRange, padding=None):
        """ Sets the range of the target.
        """
        # The padding paramater is a bit of a hack. TODO: how better?
        # viewBox.setRange doesn't accept an axis number :-(
        if self.axisNumber == X_AXIS:
            xRange, yRange = targetRange, None
        else:
            xRange, yRange = None, targetRange

        self.viewBox.setRange(xRange = xRange, yRange=yRange, padding=padding,
                              update=False, disableAutoRange=True)



class PgAxisFlipCti(BoolCti):
    """ BoolCti that flips an axis when True.
    """
    def __init__(self, viewBox, axisNumber, nodeName='flipped', defaultData=False):
        """ Constructor.
            The target axis is specified by viewBox and axisNumber (0 for x-axis, 1 for y-axis)
        """
        super(PgAxisFlipCti, self).__init__(nodeName, defaultData=defaultData)
        check_class(viewBox, pg.ViewBox)
        assert axisNumber in (X_AXIS, Y_AXIS), "axisNumber must be 0 or 1"
        self.viewBox = viewBox
        self.axisNumber = axisNumber


    def _updateTargetFromNode(self):
        """ Applies the configuration to its target axis
        """
        if self.axisNumber == X_AXIS:
            self.viewBox.invertX(self.configValue)
        else:
            self.viewBox.invertY(self.configValue)



class PgAxisLabelCti(ChoiceCti):
    """ Configuration tree item that is linked to the axis label.
    """
    NO_LABEL = '-- none --'

    def __init__(self, plotItem, axisPosition, collector,
                 nodeName='label', defaultData=0, configValues=None):
        """ Constructor
            :param plotItem:
            :param axisPosition: 'left', 'right', 'bottom', 'top'
            :param collector: needed to get the collector.getRtiInfo
            :param nodeName: the nod name of this config tree item (default = label
            :param defaultData:
            :param configValues:
        """
        super(PgAxisLabelCti, self).__init__(nodeName, editable=True,
                                             defaultData=defaultData, configValues=configValues)
        assert axisPosition in VALID_AXIS_POSITIONS,\
            "axisPosition must be in {}".format(VALID_AXIS_POSITIONS)
        self.collector = collector
        self.plotItem = plotItem
        self.axisPosition = axisPosition


    def _updateTargetFromNode(self):
        """ Applies the configuration to the target axis it monitors.
            The axis label will be set to the configValue. If the configValue equals
             PgAxisLabelCti.NO_LABEL, the label will be hidden.
        """
        rtiInfo = self.collector.getRtiInfo()
        self.plotItem.setLabel(self.axisPosition, self.configValue.format(**rtiInfo))
        self.plotItem.showLabel(self.axisPosition, self.configValue != self.NO_LABEL)



class PgAxisShowCti(BoolCti):
    """ BoolCti that toggles axisPosition showing/hiding an axis.
    """
    def __init__(self, plotItem, axisPosition, nodeName='show', defaultData=True):
        """ Constructor.
            The target axis is specified by plotItem and axisPosition.
            axisPosition must be one of: 'left', 'right', 'bottom', 'top'

            NOTE: the PyQtGraph showAxis seems not to work. TODO: investigate.
        """
        super(PgAxisShowCti, self).__init__(nodeName, defaultData=defaultData)
        assert axisPosition in VALID_AXIS_POSITIONS,\
            "axisPosition must be in {}".format(VALID_AXIS_POSITIONS)

        self.plotItem = plotItem
        self.axisPosition = axisPosition


    def _updateTargetFromNode(self):
        """ Applies the configuration to its target axis
        """
        logger.debug("showAxis: {}, {}".format(self.axisPosition, self.configValue))
        self.plotItem.showAxis(self.axisPosition, show=self.configValue) # Seems not to work


class PgAxisLogModeCti(BoolCti):
    """ BoolCti that toggles an axis between logarithmic vs linear mode.
    """
    def __init__(self, plotItem, axisNumber, nodeName='logarithmic', defaultData=False):
        """ Constructor.
            The target axis is specified by plotItem and axisNumber (0 for x-axis, 1 for y-axis)
        """
        super(PgAxisLogModeCti, self).__init__(nodeName, defaultData=defaultData)
        self.plotItem = plotItem
        self.axisNumber = axisNumber


    def _updateTargetFromNode(self):
        """ Applies the configuration to its target axis
        """
        if self.axisNumber == X_AXIS:
            xMode, yMode = self.configValue, None
        else:
            xMode, yMode = None, self.configValue

        self.plotItem.setLogMode(x=xMode, y=yMode)


class PgAxisCti(GroupCti):
    """ Configuration tree item for a PyQtGraph plot axis.

        Currently nothing more than a GroupCti.
    """
    pass



class PgPlotItemCti(GroupCti):
    """ Config tree item for manipulating a PyQtGraph.PlotItem
    """
    def __init__(self, plotItem, nodeName='axes', xAxisCti=None, yAxisCti=None):
        """ Constructor
        """
        super(PgPlotItemCti, self).__init__(nodeName)
        assert plotItem, "target plotItem is undefined"

        # x/y. How do we disable this?
        self.aspectLockedCti = self.insertChild(BoolCti("lock aspect ratio", False, expanded=False))
        self.aspectRatioCti = self.aspectLockedCti.insertChild(FloatCti("ratio", 1.0, minValue=0.0))

        self.plotItem = plotItem
        viewBox = plotItem.getViewBox()

        # Keeping references to the axes CTIs because they need to be updated quickly when
        # the range changes; getting by path may be slow.)
        if xAxisCti is None:
            self.xAxisCti = self.insertChild(PgAxisCti('x-axis'))
        else:
            check_class(xAxisCti, PgAxisCti)
            self.xAxisCti = self.insertChild(xAxisCti)

        if yAxisCti is None:
            self.yAxisCti = self.insertChild(PgAxisCti('y-axis'))
        else:
            check_class(yAxisCti, PgAxisCti)
            self.yAxisCti = self.insertChild(yAxisCti)

        if True:
            self.insertChild(ViewBoxDebugCti('viewbox state', viewBox))

        # Connect signals
        self.plotItem.autoBtn.clicked.connect(self._setAutoRangeOn)
        self.plotItem.sigClicked.connect(self._setAutoRangeOn)


    def _closeResources(self):
        """ Disconnects signals.
            Is called by self.finalize when the cti is deleted.
        """
        self.plotItem.autoBtn.clicked.disconnect(self._setAutoRangeOn)
        self.plotItem.sigClicked.disconnect(self._setAutoRangeOn)


    def _updateTargetFromNode(self):
        """ Applies the configuration to the target axis it monitors.
        """
        self.plotItem.setAspectLocked(lock=self.aspectLockedCti.configValue,
                                      ratio=self.aspectRatioCti.configValue)


    def _setAutoRangeOn(self):
        """ Turns on the auto range checkbox.
            Calls _updateTargetFromNode to calculate the new range.
        """
        logger.debug("_setAutoRangeOn")
        for axisCti in [self.xAxisCti, self.yAxisCti]:
            for childCti in axisCti.childItems:
                if isinstance(childCti, PgAxisRangeCti):
                    childCti.autoRangeCti.data = True
        self.model.itemChanged.emit(self)

