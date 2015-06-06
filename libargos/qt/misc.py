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
import sys, logging, os, traceback

from libargos import info

logger = logging.getLogger(__name__)
                
#########################
# Importing PyQt/PySide #
#########################       


# Abstracts away the differences between PySide and PyQt
USE_PYQT = True # PySide is used when False

if USE_PYQT:
    # This is only needed for Python v2 but is harmless for Python v3.
    import sip
    sip.setapi('QDate', 2)
    sip.setapi('QDateTime', 2)
    sip.setapi('QString', 2)
    sip.setapi('QTextStream', 2)
    sip.setapi('QTime', 2)
    sip.setapi('QUrl', 2)
    sip.setapi('QVariant', 2)
    

if USE_PYQT:
    from PyQt4 import QtCore, QtGui
    from PyQt4.QtCore import Qt
    from PyQt4.QtCore import pyqtSignal as QtSignal
    from PyQt4.QtCore import pyqtSlot as QtSlot 
else:
    from PySide import QtCore, QtGui
    from PySide.QtCore import Qt
    from PySide.QtCore import Signal as QtSignal
    from PySide.QtCore import Slot as QtSlot
                
                
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
    """ Initializes the QtGui.QApplication instance. Creates one if it doesn't exist.
        
        Sets Argos specific attributes, such as the OrganizationName, so that the application
        persistent settings are read/written to the correct settings file/winreg. It is therefore
        important to call this function at startup. The ArgosApplication constructor does this. 
        
        Returns the application.
    """
    # PyQtGraph requires raster graphics system.
    #graphicsSystem = "raster" # raster, native or opengl
    graphicsSystem = "raster"
    logger.info("Setting Qt graphics system to: {}".format(graphicsSystem))
    QtGui.QApplication.setGraphicsSystem(graphicsSystem)

    app = QtGui.QApplication(sys.argv)
    initArgosApplicationSettings(app)
    return app
    

def initArgosApplicationSettings(app):
    """ Sets Argos specific attributes, such as the OrganizationName, so that the application
        persistent settings are read/written to the correct settings file/winreg. It is therefore
        important to call this function at startup. The ArgosApplication constructor does this. 
    """
    assert app, \
        "app undefined. Call QtGui.QApplication.instance() or QtCor.QApplication.instance() first."

    logger.debug("Setting Argos QApplication settings.")    
    app.setApplicationName(info.REPO_NAME)
    app.setApplicationVersion(info.VERSION)
    app.setOrganizationName(info.ORGANIZATION_NAME)
    app.setOrganizationDomain(info.ORGANIZATION_DOMAIN)
    
                
######################
# Exception Handling #
######################

def handleException(exc_type, exc_value, exc_traceback):

    traceback.format_exception(exc_type, exc_value, exc_traceback)
    
    logger.error("Bug: unexpected {}".format(exc_type), 
                 exc_info=(exc_type, exc_value, exc_traceback))
    if info.DEBUGGING:
        sys.exit(1)
    else:
        # Constructing a QApplication in case this hasn't been done yet.
        if not QtGui.qApp:
            _app = QtGui.QApplication()
         
        msgBox = QtGui.QMessageBox()
        msgBox.setText("Bug: unexpected {}".format(exc_type.__name__))
        msgBox.setInformativeText(str(exc_value))
        lst = traceback.format_exception(exc_type, exc_value, exc_traceback)
        msgBox.setDetailedText("".join(lst))
        msgBox.setIcon(QtGui.QMessageBox.Warning)
        msgBox.exec_()
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
    opt = QtGui.QStyleOption()
    opt.initFrom(widget)
    style = widget.style()
    return style.subElementRect(QtGui.QStyle.SE_ViewItemCheckIndicator, opt, widget)
            
