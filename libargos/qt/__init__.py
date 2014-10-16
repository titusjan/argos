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

""" Qt specific stuff, which is not specific to this project.
"""

# Abstracts away the differences between PySide and PyQt
USE_PYQT = True # Use PySide if False

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
else:
    from PySide import QtCore, QtGui
    from PySide.QtCore import Qt


import sys, logging

from .. import info
from ..utils import check_class

logger = logging.getLogger(__name__)

def getQApplicationInstance():
    """ Returns the QApplication instance. Creates one if it doesn't exist.
    """
    app = QtGui.QApplication.instance()

    if app is None:
        app = QtGui.QApplication(sys.argv)
    check_class(app, QtGui.QApplication)
    
    app.setApplicationName(info.REPO_NAME)
    app.setApplicationVersion(info.VERSION)
    app.setOrganizationName(info.ORGANIZATION_NAME)
    app.setOrganizationDomain(info.ORGANIZATION_DOMAIN)    
    
    return app

# Keep a reference so that we canRun once so that we can call libpepeye.browse without 
# having to call getQApplicationInstance them selves (lets see if this is a good idea)
APPLICATION_INSTANCE = getQApplicationInstance()

def executeApplication():
    """ Executes all browsers by starting the Qt main application
    """  
    logger.info("Starting the browser(s)...")
    app = APPLICATION_INSTANCE
    exit_code = app.exec_()
    logger.info("Browser(s) done...")
    return exit_code
