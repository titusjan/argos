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

""" Miscellaneous functions and classes using Qt
"""
from __future__ import print_function

import logging
import os.path

from argos.qt import QtWidgets

logger = logging.getLogger(__name__)


def setWidgetSizePolicy(widget, hor=None, ver=None):
    """ Sets horizontal and/or vertical size policy on a widget
    """
    sizePolicy = widget.sizePolicy()
    logger.debug("widget {} size policy Befor: {} {}"
                 .format(widget, sizePolicy.horizontalPolicy(), sizePolicy.verticalPolicy()))

    if hor is not None:
        sizePolicy.setHorizontalPolicy(hor)

    if ver is not None:
        sizePolicy.setVerticalPolicy(ver)

    widget.setSizePolicy(sizePolicy)

    sizePolicy = widget.sizePolicy()
    logger.debug("widget {} size policy AFTER: {} {}"
                 .format(widget, sizePolicy.horizontalPolicy(), sizePolicy.verticalPolicy()))


def processEvents():
    """ Processes all pending events for the calling thread until there are no more events to
        process.
    """
    QtWidgets.QApplication.instance().processEvents()


def setApplicationQtStyle(styleName):
    """ Sets the Qt style (e.g. to 'fusion')
    """
    qApp = QtWidgets.QApplication.instance()
    logger.debug("Setting Qt style to: {}".format(styleName))
    qApp.setStyle(QtWidgets.QStyleFactory.create(styleName))
    if qApp.style().objectName().lower() != styleName.lower():
        logger.warning(
            "Setting style failed: actual style {!r} is not the specified style {!r}"
            .format(qApp.style().objectName(), styleName))


def setApplicationStyleSheet(fileName):
    """ Reads the style sheet from file and set it as application style sheet.
    """
    fileName = os.path.abspath(fileName)
    logger.debug("Reading qss from: {}".format(fileName))
    try:
        with open(fileName) as input:
            qss = input.read()
    except Exception as ex:
        logger.warning("Unable to read style sheet from '{}'. Reason: {}".format(fileName, ex))
        return

    QtWidgets.QApplication.instance().setStyleSheet(qss)



class BasePanel(QtWidgets.QFrame):
    """ Base panel from which others are derived.

        Define shape
    """
    def __init__(self, **kwargs):
        super(BasePanel, self).__init__(**kwargs)
        #self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        #self.setFrameShadow(QtWidgets.QFrame.Sunken)


