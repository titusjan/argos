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

from libargos.info import DEBUGGING
from libargos.inspector import registerDefaultInspectorPlugins
from libargos.inspector.registry import InspectorRegistry
from libargos.qt import getQApplicationInstance, QtCore
from libargos.repo.repotreemodel import RepoTreeModel
from libargos.repo.registry import globalRtiRegistry
from libargos.repo.rtiplugins import registerDefaultRtiPlugins
from libargos.utils.misc import string_to_identifier
from libargos.widgets.mainwindow import MainWindow


logger = logging.getLogger(__name__)


class ArgosApplication(object):
    """ The application singleton which holds global state.
    """
    def __init__(self):
        """ Constructor
        """
        # Call getQApplicationInstance() so that the users can call libargos.browse without 
        # having to call it themselves.
        self._qApplication = getQApplicationInstance()
        #self.qApplication.focusChanged.connect(self.focusChanged) # for debugging
        
        self._repo = RepoTreeModel()
        self._rtiRegistry = globalRtiRegistry()
        registerDefaultRtiPlugins(self._rtiRegistry) # TODO: better solution
        
        self._inspectorRegistry = InspectorRegistry()
        registerDefaultInspectorPlugins(self._inspectorRegistry)
        
        self._profile = ''
        self._mainWindows = []
        self._profileSaved = False  # boolean to prevent saving settings twice
        
        #self.loadProfile(reset=resetSettings)
        self.qApplication.lastWindowClosed.connect(self.quit) 
        
        # Call setup when the event loop starts.
        QtCore.QTimer.singleShot(0, self.setup)


    def setup(self):
        """ Called once directly after the event loop starts. 
        """
        logger.debug("ArgosApplication.setup called")
        
        # Raising all window because in OS-X window 0 is not shown.
        #self.raiseAllWindows()
        self.mainWindows[0].activateWindow() # also solves the issue
        
        
    @property
    def qApplication(self): # TODO: QtGui.qApp does the same?
        """ Returns the QApplication object
        """
        return self._qApplication

    @property
    def repo(self):
        """ Returns the global repository
        """
        return self._repo

    @property
    def rtiRegistry(self):
        """ Returns the repository tree item (rti) registry
        """
        return self._rtiRegistry
        
    @property
    def inspectorRegistry(self):
        """ Returns the repository tree item (rti) registry
        """
        return self._inspectorRegistry
        
    @property
    def profile(self):
        """ Persistent settings are associated to a profile. This allows users to save the
            program state for several usage profiles.
            Profile settings are case insensitive. 
        """
        return self._profile
    
    def focusChanged(self, old, now):
        """ Is called when the focus changes. Useful for debugging
        """
        logger.debug("Focus changed from {} to {}".format(old, now))
        
    @property
    def mainWindows(self):
        """ Returns the number of MainWindows. For read-only purposes only.
        """
        return self._mainWindows

    
    def loadFiles(self, fileNames, rtiClass=None):
        """ Loads files into the repository as repo tree items of class rtiClass.
            Auto-detects using the extensions when rtiClass is None
        """
        for fileName in fileNames:
            self.repo.loadFile(fileName, rtiClass=rtiClass)
                

    def _profileGroupName(self, profile):
        """ Returns the name of the QSetting group for this profile.
            Converts to lower case and removes whitespace, interpunction, etc.
            Prepends __debugging__ if the debugging flag is set 
        """
        profGroupName = '__debugging__' if DEBUGGING else '' 
        profGroupName += string_to_identifier(profile)
        return profGroupName
        

    def deleteProfile(self, profile):
        """ Removes a profile from the persistent settings
        """
        profGroupName = self._profileGroupName(profile)                
        logger.debug("Resetting profile settings: {}".format(profGroupName))
        settings = QtCore.QSettings()
        settings.remove(profGroupName)
        

    def deleteAllProfiles(self):
        """ Returns a list of all profiles
        """
        settings = QtCore.QSettings()
        for profGroupName in QtCore.QSettings().childGroups():
            settings.remove(profGroupName)
        
        
    def loadProfile(self, profile):
        """ Reads the persistent program settings
        """ 
        settings = QtCore.QSettings()
        logger.info("Reading profile {!r} from: {}".format(profile, settings.fileName()))
        
        self._profile = profile
        profGroupName = self._profileGroupName(profile)
    
        # Instantiate windows from groups            
        settings.beginGroup(profGroupName)
        try:
            for windowGroupName in settings.childGroups():
                if windowGroupName.startswith('window'):
                    settings.beginGroup(windowGroupName)
                    try:
                        self.addNewMainWindow(settings=settings)
                    finally:
                        settings.endGroup()
        finally:
            settings.endGroup()
            
        if len(self.mainWindows) == 0:
            logger.warn("No open windows in profile (creating one).")
            self.addNewMainWindow()
        

    def saveProfile(self):
        """ Writes the view settings to the persistent store
        """
        if not self.profile:
            logger.warning("No profile defined (no settings saved)")
            return

        self._profileSaved = True                        
                 
        settings = QtCore.QSettings()  
        logger.debug("Writing settings to: {}".format(settings.fileName()))

        profGroupName = self._profileGroupName(self.profile)
        settings.remove(profGroupName) # start with a clean slate

        assert self.mainWindows, "no main windows found"
        settings.beginGroup(profGroupName)
        try:
            for winNr, mainWindow in enumerate(self.mainWindows):
                settings.beginGroup("window-{:02d}".format(winNr))
                try:
                    mainWindow.saveProfile(settings)
                finally:
                    settings.endGroup()
        finally:
            settings.endGroup()
                        
                        
    def saveProfileIfNeeded(self):
        """ Writes the persistent settings of this profile is this is the last window and
            the settings have not yet been saved.
        """
        if not self._profileSaved and len(self.mainWindows) <= 1:
            self.saveProfile()
            
            
    def addNewMainWindow(self, settings=None):
        """ Creates and shows a new MainWindow.
        """
        mainWindow = MainWindow(self)
        self.mainWindows.append(mainWindow)
        
        if settings:
            mainWindow.readViewSettings(settings)
        
        mainWindow.show()
        if platform.system() == 'Darwin':
            # Calling raise when before the QApplication.exec_ only shows the last window
            # that was added. Therefore we also call activeWindow. However, this may not
            # always be desirable. TODO: make optional? 
            mainWindow.raise_()
            pass
            
        return mainWindow
    
    
    def removeMainWindow(self, mainWindow):
        """ Removes the mainWindow from the list of windows. Saves the settings
        """
        logger.debug("removeMainWindow called")
        self.mainWindows.remove(mainWindow)
        

    def raiseAllWindows(self):
        """ Raises all application windows.
        """
        logger.debug("raiseAllWindows called")
        for mainWindow in self.mainWindows:
            logger.debug("Raising {}".format(mainWindow._instanceNr))
            mainWindow.raise_()
            
    
    def closeAllWindows(self):
        """ Closes all windows. Save windows state to persistent settings before closing them.
        """
        self.saveProfile()
        logger.debug("ArgosApplication: Closing all windows")
        self.qApplication.closeAllWindows()
        
            
    def quit(self):
        """ Quits the application (called when the last window is closed)
        """
        logger.debug("ArgosApplication.quit called")
        assert len(self.mainWindows) == 0, \
            "Bug: still {} windows present at application quit!".format(len(self.mainWindows))
        self.qApplication.quit()


    def execute(self):
        """ Executes all main windows by starting the Qt main application
        """  
        logger.info("Starting Argos event loop...")
        exitCode = self.qApplication.exec_()
        logger.info("Argos event loop finished with exit code: {}".format(exitCode))
        return exitCode
    
            
#def createArgosApplicationFunction():
#    """ Closure to create the ArgosApplication singleton
#    """
#    globApp = ArgosApplication()
#    
#    def accessArgosApplication():
#        return globApp
#    
#    return accessArgosApplication
#
## This is actually a function definition, not a constant
##pylint: disable=C0103
#
#getArgosApplication = createArgosApplicationFunction()
#getArgosApplication.__doc__ = "Function that returns the ArgosApplication singleton"


