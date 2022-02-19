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

""" Miscellaneous Qt routines.
"""
from __future__ import division, print_function

import logging
import os
import sys
import traceback

from argos import info
from argos.qt.bindings import QtCore, QtWidgets

logger = logging.getLogger(__name__)


################
# QApplication #
################



def initQApplication():
    """ Initializes the QtWidgets.QApplication instance. Creates one if it doesn't exist.

        Sets Argos specific attributes, such as the OrganizationName, so that the application
        persistent settings are read/written to the correct settings file/winreg. It is therefore
        important to call this function at startup. The ArgosApplication constructor does this.

        Returns the application.
    """
    # PyQtGraph recommends raster graphics system for OS-X.
    if 'darwin' in sys.platform:
        graphicsSystem = "raster" # raster, native or opengl
        os.environ.setdefault('QT_GRAPHICSSYSTEM', graphicsSystem)
        logger.debug("Setting QT_GRAPHICSSYSTEM to: {}".format(graphicsSystem))

    app = QtWidgets.QApplication(sys.argv)
    initArgosApplicationSettings(app)
    return app


def initArgosApplicationSettings(app): # TODO: this is Argos specific. Move somewhere else.
    """ Sets Argos specific attributes, such as the OrganizationName, so that the application
        persistent settings are read/written to the correct settings file/winreg. It is therefore
        important to call this function at startup. The ArgosApplication constructor does this.
    """
    assert app, \
        "app undefined. Call QtWidgets.QApplication.instance() or QtCor.QApplication.instance() first."

    logger.debug("Setting Argos QApplication settings.")
    app.setApplicationName(info.REPO_NAME)
    app.setApplicationVersion(info.VERSION)
    app.setOrganizationName(info.ORGANIZATION_NAME)
    app.setOrganizationDomain(info.ORGANIZATION_DOMAIN)


######################
# Exception Handling #
######################

class ResizeDetailsMessageBox(QtWidgets.QMessageBox):
    """ Message box that enlarges when the 'Show Details' button is clicked.
        Can be used to better view stack traces. I could't find how to make a resizeable message
        box but this it the next best thing.

        Taken from:
        http://stackoverflow.com/questions/2655354/how-to-allow-resizing-of-qmessagebox-in-pyqt4
    """
    def __init__(self, detailsBoxWidth=700, detailBoxHeight=300, *args, **kwargs):
        """ Constructor
            :param detailsBoxWidht: The width of the details text box (default=700)
            :param detailBoxHeight: The heights of the details text box (default=700)
        """
        super(ResizeDetailsMessageBox, self).__init__(*args, **kwargs)
        self.detailsBoxWidth = detailsBoxWidth
        self.detailBoxHeight = detailBoxHeight


    def resizeEvent(self, event):
        """ Resizes the details box if present (i.e. when 'Show Details' button was clicked)
        """
        result = super(ResizeDetailsMessageBox, self).resizeEvent(event)

        details_box = self.findChild(QtWidgets.QTextEdit)
        if details_box is not None:
            #details_box.setFixedSize(details_box.sizeHint())
            details_box.setFixedSize(QtCore.QSize(self.detailsBoxWidth, self.detailBoxHeight))

        return result



def handleException(exc_type, exc_value, exc_traceback):

    traceback.format_exception(exc_type, exc_value, exc_traceback)

    logger.critical("Bug: uncaught {}".format(exc_type.__name__),
                    exc_info=(exc_type, exc_value, exc_traceback))
    if info.DEBUGGING:
        logger.info("Quitting application with exit code 1")
        sys.exit(1)
    else:
        # Constructing a QApplication in case this hasn't been done yet.
        if not QtWidgets.qApp:
            _app = QtWidgets.QApplication()

        msgBox = ResizeDetailsMessageBox()
        msgBox.setText("Bug: uncaught {}".format(exc_type.__name__))
        msgBox.setInformativeText(str(exc_value))
        lst = traceback.format_exception(exc_type, exc_value, exc_traceback)
        msgBox.setDetailedText("".join(lst))
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.exec_()
        logger.info("Quitting application with exit code 1")
        sys.exit(1)



######################
# QSettings routines #
######################


def getWidgetGeom(widget):
    """ Gets the QWindow or QWidget geometry as a QByteArray.

        Since Qt does not provide this directly we hack this by saving it to the QSettings
        in a temporary location and then reading it from the QSettings.

        :param widget: A QWidget that has a saveGeometry() methods
    """
    settings = QtCore.QSettings()
    settings.beginGroup('temp_conversion')
    try:
        settings.setValue("winGeom", widget.saveGeometry())
        return bytes(settings.value("winGeom"))
    finally:
        settings.endGroup()


def getWidgetState(qWindow):
    """ Gets the QWindow or QWidget state as a QByteArray.

        Since Qt does not provide this directly we hack this by saving it to the QSettings
        in a temporary location and then reading it from the QSettings.

        :param widget: A QWidget that has a saveState() methods
    """
    settings = QtCore.QSettings()
    settings.beginGroup('temp_conversion')
    try:
        settings.setValue("winState", qWindow.saveState())
        return bytes(settings.value("winState"))
    finally:
        settings.endGroup()



######################
# Debugging routines #
######################

def printChildren(obj, indent=""):
    """ Recursively prints the children of a QObject. Useful for debugging.
    """
    children=obj.children()
    if children==None:
        return
    for child in children:
        try:
            childName = child.objectName()
        except AttributeError:
            childName = "<no-name>"

        #print ("{}{:10s}: {}".format(indent, childName, child.__class__))
        print ("{}{!r}: {}".format(indent, childName, child.__class__))
        printChildren(child, indent + "    ")


def printAllWidgets(qApplication, ofType=None):
    """ Prints list of all widgets to stdout (for debugging)
    """
    print ("Application's widgets {}".format(('of type: ' + str(ofType)) if ofType else ''))
    for widget in qApplication.allWidgets():
        if ofType is None or isinstance(widget, ofType):
            print ("  {!r}".format(widget))


#####################
# Unsorted routines #
#####################


def widgetSubCheckBoxRect(widget, option):
    """ Returns the rectangle of a check box drawn as a sub element of widget
    """
    opt = QtWidgets.QStyleOption()
    opt.initFrom(widget)
    style = widget.style()
    return style.subElementRect(QtWidgets.QStyle.SE_ViewItemCheckIndicator, opt, widget)



def setWidgetSizePolicy(widget, horPolicy=None, verPolicy=None):
    """ Sets the size policy of a widget.
    """
    sizePolicy = widget.sizePolicy()

    if horPolicy is not None:
        sizePolicy.setHorizontalPolicy(horPolicy)

    if verPolicy is not None:
        sizePolicy.setVerticalPolicy(verPolicy)

    widget.setSizePolicy(sizePolicy)
    return sizePolicy

