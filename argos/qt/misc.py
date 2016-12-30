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

from argos.external.six import PY3
from argos import info
from argos.utils.cls import environment_var_to_bool

logger = logging.getLogger(__name__)

#########################
# Importing PyQt/PySide #
#########################

# Argos requires PyQt5. However, if you install qtpy (the master branch or the next version > 1.1.2)
# and set the ARGOS_USE_QTPY environment variable to "1", Argos will work with PyQt4 or PySide.
# You then can force which Qt bindings are used by setting the QT_API environment variable to pyqt5,
# pyqt4 or pyside. If the QT_API environment variable is not set, qtpy will autodetect the bindings.
#
# Note that PyQt4 and PySide or not officially supported! There are already enough dependencies
# that can vary (Python 2 & 3, Windows & Linux & OS-X, etc) so I don't want to support even more
# combinations. I keep PyQt4 and PySide working as long as it is practical but I don't do extensive
# testing. If you encounter issues with PyQt4/PySide please report them and I'll see what I can do.
# Note that pyside does currently not work in combination with Python3!


USE_QTPY = environment_var_to_bool(os.environ.get('ARGOS_USE_QTPY', False))

if USE_QTPY:
    if info.DEBUGGING:
        logger.debug("ARGOS_USE_QTPY = {}, using qtpy to find Qt bindings".format(USE_QTPY))

    import qtpy._version
    from qtpy import QtCore, QtGui, QtWidgets, QtSvg
    from qtpy.QtCore import Qt
    from qtpy.QtCore import Signal as QtSignal
    from qtpy.QtCore import Slot as QtSlot
    from qtpy import PYQT_VERSION
    from qtpy import QT_VERSION

    QT_API = qtpy.API
    QT_API_NAME = qtpy.API_NAME
    QTPY_VERSION = '.'.join(map(str, qtpy._version.version_info))
    ABOUT_QT_BINDINGS = "{} (api {}, qtpy: {})".format(QT_API_NAME, QT_API, QTPY_VERSION)

    if qtpy._version.version_info <= (1, 1, 2):
        # At least commit e863f422c7ef78f66223adaa40d52cba4a3b2fce
        logger.warning("You need qtpy version > 1.1.2, got: {}".format(QTPY_VERSION))

    # PySide in combination with Python-3 gives the following error:
    # TypeError: unhashable type: 'PgImagePlot2dCti'
    # I don't know a fix and as long as the future of PySide2 is unclear I won't spend time on it.
    if QT_API == 'pyside' and PY3:
        raise ImportError("PySide in combination with Python 3 is buggy in Argos and supported.")


else:
    if info.DEBUGGING:
        logger.debug("ARGOS_USE_QTPY = {}, using PyQt5 directly".format(USE_QTPY))

    from PyQt5 import QtCore, QtGui, QtWidgets, QtSvg
    from PyQt5.QtCore import Qt
    from PyQt5.QtCore import pyqtSignal as QtSignal
    from PyQt5.QtCore import pyqtSlot as QtSlot
    from PyQt5.Qt import PYQT_VERSION_STR as PYQT_VERSION
    from PyQt5.Qt import QT_VERSION_STR as QT_VERSION

    QT_API = ''
    QT_API_NAME = 'PyQt5'
    QTPY_VERSION = ''
    ABOUT_QT_BINDINGS = 'PyQt5'



################
# QApplication #
################


def initQCoreApplication():
    """ Initializes the QtCore.QApplication instance. Creates one if it doesn't exist.

        Sets Argos specific attributes, such as the OrganizationName, so that the application
        persistent settings are read/written to the correct settings file/winreg. It is therefore
        important to call this function (or initQApplication) at startup.

        Returns the application.
    """
    app = QtCore.QCoreApplication(sys.argv)
    initArgosApplicationSettings(app)
    return app


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
        logger.info("Setting QT_GRAPHICSSYSTEM to: {}".format(graphicsSystem))

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

def removeSettingsGroup(groupName, settings=None):
    """ Removes a group from the persistent settings
    """
    logger.debug("Removing settings group: {}".format(groupName))
    settings = QtCore.QSettings() if settings is None else settings
    settings.remove(groupName)


def containsSettingsGroup(groupName, settings=None):
    """ Returns True if the settings contain a group with the name groupName.
        Works recursively when the groupName is a slash separated path.
    """
    def _containsPath(path, settings):
        "Aux function for containsSettingsGroup. Does the actual recursive search."
        if len(path) == 0:
            return True
        else:
            head = path[0]
            tail = path[1:]
            if head not in settings.childGroups():
                return False
            else:
                settings.beginGroup(head)
                try:
                    return _containsPath(tail, settings)
                finally:
                    settings.endGroup()

    # Body starts here
    path = os.path.split(groupName)
    logger.debug("Looking for path: {}".format(path))
    settings = QtCore.QSettings() if settings is None else settings
    return _containsPath(path, settings)

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

