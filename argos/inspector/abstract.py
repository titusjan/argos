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

""" Base class for inspectors
"""
import logging
from argos.config.groupcti import MainGroupCti
from argos.info import DEBUGGING
from argos.qt import QtWidgets, QtSlot
from argos.utils.cls import type_name, check_class
from argos.widgets.constants import DOCK_SPACING, DOCK_MARGIN
from argos.widgets.display import MessageDisplay

logger = logging.getLogger(__name__)

class InvalidDataError(Exception):
    """ Exception that should be raised if the inspector cannot handle this type of data.
        Can be used to distuingish the situation from other exceptions an then, for example,
        draw an empty plot instead of the error message pane.
    """
    pass


class UpdateReason(object):
    """ Enumeration class that contains the reason for updating the inspector contents.
    """
    NEW_MAIN_WINDOW     = "new main window"
    INSPECTOR_CHANGED   = "inspector changed"
    RTI_CHANGED         = "repo tree item changed"
    COLLECTOR_COMBO_BOX = "collector combobox changed"
    COLLECTOR_SPIN_BOX  = "collector spinbox changed"
    CONFIG_CHANGED      = "config changed"

    __VALID_REASONS = (NEW_MAIN_WINDOW, INSPECTOR_CHANGED, RTI_CHANGED,
                       COLLECTOR_COMBO_BOX, COLLECTOR_SPIN_BOX, CONFIG_CHANGED)


    @classmethod
    def validReasons(cls):
        """ Returns a tuple with all valid reasond
        """
        return cls.__VALID_REASONS


    @classmethod
    def checkValid(cls, reason):
        """ Raises ValueError if the reason is not one of the valid enumerations
        """
        if reason not in cls.__VALID_REASONS:
            raise ValueError("reason must be one of {}, got {}".format(cls.__VALID_REASONS, reason))



class AbstractInspector(QtWidgets.QStackedWidget):
    """ Abstract base class for inspectors.
        An inspector is a stacked widget; it has a contents page and and error page.
    """
    _fullName = "base" # see the fullName() class method for explanation
    ERROR_PAGE_IDX = 0
    CONTENTS_PAGE_IDX = 1

    def __init__(self, collector, parent=None):
        """ Constructor.

            When subclassing the AbstractInspector try to minimize the work done in the constructor.
            Place all functionality that may raise an exception in updateContents or clearContents,
            these functions will show an error page and prevent the application from aborting. If
            an exception occurs in the constructor it is not caught!

            :param collector: the data collector from where this inspector gets its data
            :param parent: parent widget.
        """

        super(AbstractInspector, self).__init__(parent)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self._config = MainGroupCti(nodeName='inspector') # Is typically redefined.
        self._collector = collector

        self.errorWidget = MessageDisplay()
        self.addWidget(self.errorWidget)

        self.contentsWidget = QtWidgets.QWidget()
        self.addWidget(self.contentsWidget)

        self.contentsLayout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom)
        self.contentsLayout.setSpacing(DOCK_SPACING)
        self.contentsLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)
        self.contentsWidget.setLayout(self.contentsLayout)

        self.setCurrentIndex(self.CONTENTS_PAGE_IDX)


    def finalize(self):
        """ Is called before destruction. Can be used to clean-up resources
        """
        logger.debug("Finalizing: {}".format(self))


    @property
    def config(self):
        """ The root config tree item for this inspector.
        """
        return self._config


    @property
    def windowNumber(self):
        """ The instance number of the window this inspector belongs to.
        """
        return self.collector.windowNumber


    @classmethod
    def descriptionHtml(cls):
        """ A long description that will be displayed as help in the inspector-open dialog box.
        """
        return ""


    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.

            This determines the dimensionality of the inspector. For example an inspector that shows
            an image, and has axes names 'X' and 'Y', is 2-dimensional. Also the slicedArray that
            will be returned by the collector will then be 2-dimensional. This invariant also holds
            when the axesNames is an empty tuple. The slicedArray will then be zero-dimensional.
            For a 0-D example, see qtplugins.text.TextInspector.

            The axesNames should be row-first, so in this example: ['Y', 'X']

            The names should not include the string "Axis"; the Collector.fullAxisNames()
            returns that.
        """
        return tuple()


    @property
    def collector(self):
        """ The data collector from where this inspector gets its data
        """
        return self._collector


    def configValue(self, nodePath):
        """ Returns the config value data at the node path
        """
        return self.config.findByNodePath(nodePath).configValue


    def updateContents(self, reason=None, initiator=None): # TODO: reason mandatory?
        """ Tries to draw the widget contents with the updated RTI.
            Shows the error page in case an exception is raised while drawing the contents.
            Descendants should override _drawContents, not updateContents.

            During the call of _drawContents, the updating of the configuration tree is blocked to
            avoid circular effects. After that, a call to self.config.refreshFromTarget() is
            made to refresh the configuration tree with possible new values from the inspector
            (the inspector is the configuration's target, hence the name).

            The reason parameter is a string (one of the UpdateReason values) that indicates why
            the inspector contents whas updated. This can, for instance, be used to optimize
            drawing the inspector contents. Note that the reason may be undefined (None).

            The initiator may contain the object that initiated the updated. The type depends on the
            reason. At the moment the initiator is only implemented for the "config changed" reason. In
            this case the initiator will be the Config Tree Item (CTI that has changed).
        """
        UpdateReason.checkValid(reason)
        logger.debug("---- Inspector updateContents, reason: {}, initiator: {}"
                     .format(reason, initiator))
        logger.debug("Inspector: {}".format(self))
        logger.debug("RTI: {}".format(self.collector.rti))
        try:
            self.setCurrentIndex(self.CONTENTS_PAGE_IDX)

            wasBlocked = self.config.model.setRefreshBlocked(True)
            try:
                self._drawContents(reason=reason, initiator=initiator)
                logger.debug("_drawContents finished successfully")

                # Update the config tree from the (possibly) new state of the PgLinePlot1d inspector,
                # e.g. the axis range may have changed while drawing.
                # self.config.updateTarget() # TODO: enable this here (instead of doing it in the inspector._drawContents when needed)?
            finally:
                self.config.model.setRefreshBlocked(wasBlocked)

            # Call refreshFromTarget in case the newly applied configuration resulted in a change
            # of the state of the configuration's target's (i.e. the inspector state)
            logger.debug("_drawContents finished successfully, calling refreshFromTarget...")
            self.config.refreshFromTarget()
            logger.debug("refreshFromTarget finished successfully")

        except InvalidDataError as ex:
            logger.info("Unable to draw the inspector contents: {}".format(ex))

        except Exception as ex:
            if DEBUGGING:  # TODO: enable
                raise
            logger.error("Error while drawing the inspector: {} ----".format(ex))
            logger.exception(ex)
            self._clearContents()
            self.setCurrentIndex(self.ERROR_PAGE_IDX)
            self._showError(msg=str(ex), title=type_name(ex))
        else:
            logger.debug("---- updateContents finished successfully")


    def _drawContents(self, reason=None, initiator=None):
        """ Is called by updateContents to do the actual drawing.
            Descendants should override _drawContents and not worry about exceptions;
            the updateContents will show the error page if an exception is raised.

            See the updateContents() docstring for the reason and initiator parameters.
        """
        raise NotImplementedError()


    def _clearContents(self):
        """ Override to clear the widget contents.

            Is called to empty the inspector when an exception occurs during _drawContents,
            to prevent further errors.
        """
        raise NotImplementedError()


    def _showError(self, msg="", title="Error"):
        """ Shows an error message.
        """
        self.errorWidget.setError(msg=msg, title=title)

