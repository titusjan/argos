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

""" Version and other info for this program
"""
import logging, platform

from libargos.qt import getQApplicationInstance
from libargos.widgets.mainwindow import MainWindow

logger = logging.getLogger(__name__)

class ArgosApplication(object):
    """ The application singleton which holds global stat
    """
    def __init__(self):
        """ Constructor
        """
        # Keep a reference so that users can call libargos.browse without having to call 
        # getQApplicationInstance them selves (lets see if this is a good idea)
        self.qApplicationInstance = getQApplicationInstance()
    
        self._mainWindows = []
    
    
    def createMainWindow(self, fileNames = tuple(), **kwargs):
        """ Creates and shows a new MainWindow.
            All fileNames in the fileNames list are opened
            The **kwargs are passed on to the MainWindow constructor.
        """
        # Assumes qt.getQApplicationInstance() has been executed.
        mainWindow = MainWindow(**kwargs)
        self._mainWindows.append(mainWindow)
        mainWindow.openFiles(fileNames=fileNames)
        mainWindow.show()
        if platform.system() == 'Darwin':
            mainWindow.raise_()
        return mainWindow


    def execute(self):
        """ Executes all main windows by starting the Qt main application
        """  
        logger.info("Starting the Argos...")
        exitCode = self.qApplicationInstance.exec_()
        logger.info("Argos finished with exit code: {}".format(exitCode))
        return exitCode
    
    
    
def createArgosApplicationFunction():
    """ Closure to create the ArgosApplication singleton
    """
    globApp = ArgosApplication()
    
    def accessArgosApplication():
        return globApp
    
    return accessArgosApplication

# This is actually a function definition, not a constant
#pylint: disable=C0103

getArgosApplication = createArgosApplicationFunction()
getArgosApplication.__doc__ = "Function that returns the ArgosApplication singleton"


