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
import sys, logging, platform

from libargos.info import DEBUGGING, DEFAULT_PROFILE
from libargos.inspector.registry import InspectorRegistry
from libargos.qt import QtCore
from libargos.qt.misc import removeSettingsGroup, handleException, initQApplication
from libargos.qt.registry import GRP_REGISTRY
from libargos.repo.repotreemodel import RepoTreeModel
from libargos.repo.registry import globalRtiRegistry
from libargos.utils.misc import string_to_identifier
from libargos.widgets.mainwindow import MainWindow
from libargos.widgets.pluginsdialog import PluginsDialog

logger = logging.getLogger(__name__)


def browse(fileNames = None, 
           inspectorId=None, 
           profile=DEFAULT_PROFILE, 
           resetProfile=False, 
           resetAllProfiles=False, 
           resetRegistry=False): 
    """ Opens the main window(s) for the persistent settings of the given profile, 
        and executes the application.
    """
    #if DEBUGGING: # TODO temporary
    #    _gcMon = createGcMonitor()
    
    # Create
    argosApp = ArgosApplication()
            
    if resetProfile:
        argosApp.deleteProfile(profile)
    if resetAllProfiles:
        argosApp.deleteAllProfiles()
    if resetRegistry:
        argosApp.deleteRegistries()

    # Must be called before opening the files so that file format are auto-detected.
    argosApp.loadOrInitRegistries()
        
    # Load data in common repository before windows are created.
    argosApp.loadFiles(fileNames)
    if DEBUGGING:
        __addTestData(argosApp)
    
    # Create windows for this profile.     
    argosApp.loadProfile(profile=profile, inspectorId=inspectorId)

    return argosApp.execute()


def __addTestData(argosApp):
    """ Temporary function to add test data
    """
    import numpy as np
    from libargos.repo.memoryrtis import MappingRti
    myDict = {}
    myDict['name'] = 'Pac Man'
    myDict['age'] = 34
    myDict['ghosts'] = ['Inky', 'Blinky', 'Pinky', 'Clyde']
    myDict['array'] = np.arange(24).reshape(3, 8)
    myDict['subDict'] = {'mean': np.ones(111), 'stddev': np.zeros(111, dtype=np.uint16)}
    
    mappingRti = MappingRti(myDict, nodeName="myDict", fileName='')
    argosApp.repo.insertItem(mappingRti)


class ArgosApplication(object):
    """ The application singleton which holds global state.
    """
    def __init__(self, setExceptHook=True):
        """ Constructor
        
            :param setExceptHook: Sets the global sys.except hook so that Qt shows a dialog box 
                when an exception is raised.
    
                In debugging mode, the program will just quit in case of an exception. This is 
                standard Python behavior but PyQt and PySide swallow exceptions by default (only a 
                log message is displayed). The practice of swallowing exceptions fosters bad 
                programming IHMO as it is easy to miss errors. I strongly recommend that you set
                the setExceptHook to True.
        """
        # Call initQtGuiApplicationInstance() so that the users can call libargos.browse without 
        # having to call it themselves.
        self._qApplication = initQApplication()
        
        if setExceptHook:
            logger.debug("Setting sys.excepthook to Argos exception handling")
            sys.excepthook = handleException
        
        #self.qApplication.focusChanged.connect(self.focusChanged) # for debugging
        
        self._repo = RepoTreeModel()
        self._rtiRegistry = globalRtiRegistry()
        self._inspectorRegistry = InspectorRegistry()
        
        self._profile = ''
        self._mainWindows = []
        self._settingsSaved = False  # boolean to prevent saving settings twice
        
        self.pluginsDialog = PluginsDialog(parent=None,
                                inspectorRegistry=self.inspectorRegistry, 
                                rtiRegistry=self.rtiRegistry)
                
        self.qApplication.lastWindowClosed.connect(self.quit) 
        
        # Call setup when the event loop starts.
        QtCore.QTimer.singleShot(0, self.setup)


    def setup(self):
        """ Called once directly after the event loop starts. 
        """
        logger.debug("ArgosApplication.setup called")
        
        # Raising all window because in OS-X window 0 is not shown.
        #self.raiseAllWindows()
        # activateWindow also solves the issue but doesn't work with the --inspector option.
        self.mainWindows[0].activateWindow() 
        
        self.pluginsDialog.refresh()
        
        
    @property
    def qApplication(self):
        """ Returns the QApplication object. Equivalent to QtGui.qApp.
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
        """ Is called when the focus changes. Useful for debugging.
        """
        logger.debug("Focus changed from {} to {}".format(old, now))
        
        
    @property
    def mainWindows(self):
        """ Returns the list of MainWindows. For read-only purposes only.
        """
        return self._mainWindows

                                
    def deleteRegistries(self):
        """ Deletes all registry information from the persistent store.
        """
        removeSettingsGroup(GRP_REGISTRY)
                                

    def loadOrInitRegistries(self):
        """ Reads the registry persistent program settings
        """
        self.inspectorRegistry.loadOrInitSettings()
        self.rtiRegistry.loadOrInitSettings()
        

#    def saveRegistries(self):
#        """ Writes the view settings to the persistent store
#        """
#        self.rtiRegistry.saveSettings(self.GRP_REGISTRY_RTI)
#        self.inspectorRegistry.saveSettings(self.GRP_REGISTRY_INSPECTORS)
        
        
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
        
        
    def loadProfile(self, profile, inspectorId=None):
        """ Reads the persistent program settings for the current profile.
        
            If inspectorId is given, a window with this inspector will be created if it wasn't
            already created in the profile. All windows with this inspector will be raised.
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
            
        if inspectorId is not None:
            windows = [win for win in self._mainWindows if win.inspectorId == inspectorId]
            if len(windows) == 0:
                logger.info("Creating window for inspector: {!r}".format(inspectorId))
                try:
                    win = self.addNewMainWindow(inspectorId=inspectorId)
                except KeyError:
                    logger.warn("No inspector found with ID: {}".format(inspectorId))
            else:
                for win in windows:
                    win.raise_()
            
        if len(self.mainWindows) == 0:
            logger.warn("No open windows in profile (creating one).")
            #self.addNewMainWindow(inspectorId='Qt/Table')
            self.addNewMainWindow(inspectorId='Empty inspector')
            
        

    def saveProfile(self):
        """ Writes the current profile settings to the persistent store
        """
        if not self.profile:
            logger.warning("No profile defined (no settings saved)")
            return

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


    def saveSettings(self):
        """ Saves the persistent settings. Only saves the profile.
        """
        try:
            self.saveProfile()
        except Exception as ex:
            # Continue, even if saving the settings fails.
            logger.warn(ex)
            if DEBUGGING:
                raise
        finally:    
            self._settingsSaved = True     
                           
                                                
    def saveSettingsIfNeeded(self):
        """ Writes the persistent settings of this profile is this is the last window and
            the settings have not yet been saved.
        """
        if not self._settingsSaved and len(self.mainWindows) <= 1:
            self.saveSettings()
            
    
    def loadFiles(self, fileNames, rtiClass=None):
        """ Loads files into the repository as repo tree items of class rtiClass.
            Auto-detects using the extensions when rtiClass is None
        """
        for fileName in fileNames:
            self.repo.loadFile(fileName, rtiClass=rtiClass)
            
            
    def addNewMainWindow(self, settings=None, inspectorId=None):
        """ Creates and shows a new MainWindow.
        
            If inspectorId is set, it will set the identifier from that ID.
            If the inspector identifier is not found in the registry, a KeyError is raised.
        """
        mainWindow = MainWindow(self)
        
        if settings:
            mainWindow.readViewSettings(settings)
        
        if inspectorId:
            mainWindow.setInspectorById(inspectorId)
            
        self.mainWindows.append(mainWindow)
        mainWindow.drawWindowContents()
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
        self.saveSettings()
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
    
