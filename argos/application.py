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
import json
import logging
import os.path
import pprint
import sys

from argos.info import DEBUGGING, EXIT_CODE_SUCCESS
from argos.inspector.registry import InspectorRegistry, DEFAULT_INSPECTOR
from argos.qt import QtCore, QtWidgets, QtSlot
from argos.qt.misc import handleException, initQApplication
from argos.reg.basereg import nameToIdentifier
from argos.repo.colors import CmLibSingleton, DEF_FAV_COLOR_MAPS
from argos.repo.registry import globalRtiRegistry
from argos.repo.repotreemodel import RepoTreeModel
from argos.utils.dirs import argosConfigDirectory, normRealPath, ensureFileExists
from argos.widgets.mainwindow import MainWindow, UpdateReason

logger = logging.getLogger(__name__)


_Q_APP = None # Keep reference to QApplication instance to prevent garbage collection


def qApplicationSingleton():
    """ Returns the QApplication object. Creates it if it doesn't exist.

        :rtype QtWidgets.QApplication:
    """
    global _Q_APP

    qApp = QtWidgets.QApplication.instance()
    if qApp is None:
        _Q_APP = qApp = QtWidgets.QApplication([])

    return qApp


class ArgosApplication(QtCore.QObject):
    """ The application singleton which holds global state.
    """
    def __init__(self, settingsFile=None, setExceptHook=True):
        """ Constructor
            :param settingsFile: Config file from which the persistent settings are loaded.

            :param setExceptHook: Sets the global sys.except hook so that Qt shows a dialog box
                when an exception is raised.

                In debugging mode, the program will just quit in case of an exception. This is
                standard Python behavior but PyQt and PySide swallow exceptions by default (only a
                log message is displayed). The practice of swallowing exceptions fosters bad
                programming IHMO as it is easy to miss errors. I strongly recommend that you set
                the setExceptHook to True.
        """
        super(ArgosApplication, self).__init__()

        if not settingsFile:
            settingsFile = ArgosApplication.defaultSettingsFile()
            logger.debug("No config file specified. Using default: {}".format(settingsFile))

        self._settingsFile = ArgosApplication.userConfirmedSettingsFile(
            settingsFile, createWithoutConfirm=ArgosApplication.defaultSettingsFile())

        if setExceptHook:
            logger.debug("Setting sys.excepthook to Argos exception handling")
            sys.excepthook = handleException

        if DEBUGGING:
            self.qApplication.focusChanged.connect(self.focusChanged) # for debugging

        self._repo = RepoTreeModel()
        self._rtiRegistry = globalRtiRegistry()
        self._inspectorRegistry = InspectorRegistry()

        self._mainWindows = []
        self._settingsSaved = False  # boolean to prevent saving settings twice

        #self.qApplication.lastWindowClosed.connect(self.quit)
        self.qApplication.aboutToQuit.connect(self.aboutToQuitHandler)

        # Activate-actions for all windows
        self.windowActionGroup = QtWidgets.QActionGroup(self)
        self.windowActionGroup.setExclusive(True)

        # Call setup when the event loop starts.
        QtCore.QTimer.singleShot(0, self.setup)


    def setup(self):
        """ Called once directly after the event loop starts.
        """
        logger.debug("ArgosApplication.setup called")

        # Raising all window because in OS-X window 0 is not shown.
        #self.raiseAllWindows()
        # activateWindow also solves the issue but doesn't work with the --inspector option.
        actions = self.windowActionGroup.actions()
        if actions:
            actions[0].trigger()


    @classmethod
    def defaultSettingsFile(cls):
        """ Returns the path to the default settings file
        """
        return normRealPath(os.path.join(argosConfigDirectory(), 'settings.json'))


    @classmethod
    def userConfirmedSettingsFile(cls, settingsFile, createWithoutConfirm=None):
        """ Asks the user to confirm creating the settings file if it does not exist and is not
            in the createWithoutConfirm list.

            If settingsFile is a relative path it will be concatenated to the argos config dir.

            :returns: The path of the setting file.
        """
        settingsFile = os.path.join(argosConfigDirectory(), settingsFile)
        logger.debug("Testing if settings file exists: {}".format(settingsFile))
        if os.path.exists(settingsFile):
            return settingsFile
        else:
            if settingsFile in createWithoutConfirm:
                return ensureFileExists(settingsFile)
            else:
                _app = qApplicationSingleton() # make sure QApplication exists.
                button = QtWidgets.QMessageBox.question(
                    None, "Create settings file?",
                    "The setting file cannot be found: {} \n\nCreate new config file?"
                                                        .format(settingsFile))

                if button == QtWidgets.QMessageBox.Yes:
                    return ensureFileExists(settingsFile)
                else:
                    logger.warning("No settings file created. Argos won't save persistent settings.")
                    return None


    ##############
    # Properties #
    ##############

    @property
    def qApplication(self):
        """ Returns the QApplication object. Equivalent to QtWidgets.qApp.

            :rtype QtWidgets.QApplication:
        """
        # TODO: replace the lines below by qApplicationSingleton()
        global _Q_APP

        qApp = QtWidgets.QApplication.instance()
        if qApp is None:
            logger.debug("Creating QApplication")
            _Q_APP = qApp = initQApplication()

        return qApp


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
    def mainWindows(self):
        """ Returns the list of MainWindows. For read-only purposes only.
        """
        return self._mainWindows


    @property
    def settingsFile(self):
        """ Returns the name of the settings file
        """
        return self._settingsFile


    ###########
    # Methods #
    ###########

    def focusChanged(self, old, now):
        """ Is called when the focus changes. Useful for debugging.
        """
        logger.debug("Focus changed from {} to {}".format(old, now))


    def marshall(self):
        """ Returns a dictionary to save in the persistent settings
        """
        cfg = {}
        cmLib = CmLibSingleton.instance()
        cfg['cmFavorites'] = [colorMap.key for colorMap in cmLib.color_maps
                     if colorMap.meta_data.favorite]
        logger.debug("cmFavorites: {}".format(cfg['cmFavorites']))

        cfg['plugins'] = {}
        cfg['plugins']['inspectors'] = self.inspectorRegistry.marshall()
        cfg['plugins']['file-formats'] = self.rtiRegistry.marshall()

        # Save windows as a dict instead of a list to improve readability of the resulting JSON
        cfg['windows'] = {}
        for winNr, mainWindow in enumerate(self.mainWindows):
            key = "win-{:d}".format(winNr)
            cfg['windows'][key] = mainWindow.marshall()

        return cfg


    def unmarshall(self, cfg, inspectorFullName):
        """ Initializes itself from a config dict form the persistent settings.

            :param inspectorFullName: If given a window with this inspector is created.
            If an inspector window with this inspector is created from the config file, this
            parameter is ignored.
        """
        cmLib = CmLibSingleton.instance()
        if not cmLib.color_maps:
            logger.warning("No color maps loaded yet. Favorites will be empty.")
            if DEBUGGING:
                assert False, "No color maps loaded yet. Favorites will be empty."

        favKeys = cfg.get('cmFavorites', DEF_FAV_COLOR_MAPS)
        for colorMap in cmLib.color_maps:
            colorMap.meta_data.favorite = colorMap.key in favKeys

        pluginCfg = cfg.get('plugins', {})

        self.inspectorRegistry.unmarshall(pluginCfg.get('inspectors', {}))
        self.rtiRegistry.unmarshall(pluginCfg.get('file-formats', {}))

        for winId, winCfg in cfg.get('windows', {}).items():
            assert winId.startswith('win-'), "Win ID doesnt't start with 'win-': {}".format(winId)
            self.addNewMainWindow(cfg=winCfg)

        if inspectorFullName is not None:
            windows = [win for win in self._mainWindows
                       if win.inspectorFullName == inspectorFullName]
            if len(windows) == 0:
                logger.info("Creating window for inspector: {!r}".format(inspectorFullName))
                try:
                    win = self.addNewMainWindow(inspectorFullName=inspectorFullName)
                except KeyError:
                    logger.warning("No inspector found with ID: {}".format(inspectorFullName))
            else:
                for win in windows:
                    win.raise_()

        if len(self.mainWindows) == 0:
            logger.info("No open windows in settings or command line (creating one).")
            self.addNewMainWindow(inspectorFullName=DEFAULT_INSPECTOR)


    def saveSettings(self):
        """ Saves the persistent settings to file.
        """
        try:
            if not self._settingsFile:
                logger.info("No settings file specified. Not saving persistent state.")
            else:
                logger.info("Saving settings to: {}".format(self._settingsFile))
                settings = self.marshall()
                logger.debug("File formats: {}".format(settings['plugins']['file-formats']))
                try:
                    jsonStr = json.dumps(settings, sort_keys=True, indent=4)
                except Exception as ex:
                    logger.error("Failed to serialize settings to JSON: {}".format(ex))
                    logger.error("Settings: ...\n" + pprint.pformat(settings, width=100))
                    raise
                else:
                    with open(self._settingsFile, 'w') as settingsFile:
                        settingsFile.write(jsonStr)

        except Exception as ex:
            # Continue, even if saving the settings fails.
            logger.exception(ex)
            if DEBUGGING:
                raise
        finally:
            self._settingsSaved = True


    def loadSettings(self, inspectorFullName):
        """ Loads the settings from file and populates the application object from it.

            :param inspectorFullName: If given a window with this inspector is created.
                If an inspector window with this inspector is created from the config file, this
                parameter is ignored.
        """
        cfg = {}

        if not os.path.exists(self._settingsFile):
            logger.warning("Settings file does not exist: {}".format(self._settingsFile))

        try:
            with open(self._settingsFile, 'r') as settingsFile:
                jsonStr = settingsFile.read()

            if jsonStr:
                cfg = json.loads(jsonStr)
            else:
                cfg = {}
        except Exception as ex:
            logger.error("Error {} while reading settings file: {}"
                           .format(ex, self._settingsFile))
            raise # in case of a syntax error it's probably best to exit. TODO: default cfg?

        self.unmarshall(cfg, inspectorFullName)  # Always call unmarshall.


    def saveSettingsIfLastWindow(self):
        """ Writes the persistent settings if this is the last window and the settings have not yet
            been saved.
        """
        if not self._settingsSaved and len(self.mainWindows) <= 1:
            self.saveSettings()


    def loadFiles(self, fileNames):
        """ Loads files into the repository as repo tree items of class rtiClass.
            Auto-detects using the extensions when rtiClass is None
        """
        for fileName in fileNames:
            self.repo.loadFile(fileName, rtiRegItem=None)


    def repopulateAllWindowMenus(self):
        """ Repopulates the Window menu of all main windows from scratch.

            To be called when a main window is created or removed.
        """
        for win in self.mainWindows:
            win.repopulateWindowMenu(self.windowActionGroup)


    @QtSlot()
    def addNewMainWindow(self, cfg=None, inspectorFullName=None):
        """ Creates and shows a new MainWindow.

            If inspectorFullName is set, it will set the identifier from that name.
            If the inspector identifier is not found in the registry, a KeyError is raised.
        """
        mainWindow = MainWindow(self)
        self.mainWindows.append(mainWindow)

        self.windowActionGroup.addAction(mainWindow.activateWindowAction)
        self.repopulateAllWindowMenus()

        if cfg:
            mainWindow.unmarshall(cfg)

        if inspectorFullName:
            inspectorId = nameToIdentifier(inspectorFullName)
            mainWindow.setInspectorById(inspectorId)

        if mainWindow.inspectorRegItem: # can be None at start
            inspectorId = mainWindow.inspectorRegItem.identifier
            mainWindow.getInspectorActionById(inspectorId).setChecked(True)
            logger.info("Created new window with inspector: {}"
                        .format(mainWindow.inspectorRegItem.name))
        else:
            logger.info("Created new window without inspector")

        mainWindow.drawInspectorContents(reason=UpdateReason.NEW_MAIN_WINDOW)
        mainWindow.show()

        if sys.platform.startswith('darwin'):
            # Calling raise before the QApplication.exec_ only shows the last window
            # that was added. Therefore we also call activeWindow. However, this may not
            # always be desirable. TODO: make optional?
            mainWindow.raise_()
            pass

        return mainWindow


    def removeMainWindow(self, mainWindow):
        """ Removes the mainWindow from the list of windows. Saves the settings
        """
        logger.debug("removeMainWindow called")

        self.windowActionGroup.removeAction(mainWindow.activateWindowAction)
        self.repopulateAllWindowMenus()

        self.mainWindows.remove(mainWindow)


    def raiseAllWindows(self):
        """ Raises all application windows.
        """
        logger.debug("raiseAllWindows called")
        for mainWindow in self.mainWindows:
            logger.debug("Raising {}".format(mainWindow._instanceNr))
            mainWindow.raise_()


    def exit(self, exitCode):
        """ Saves settings and exits the program with a certain exit code.
        """
        self.saveSettings()
        self.qApplication.closeAllWindows()
        self.qApplication.exit(exitCode)


    def quit(self):
        """ Saves settings and exits the program with exit code 0 (success).
        """
        self.exit(EXIT_CODE_SUCCESS)


    def aboutToQuitHandler(self):
        """ Called by Qt when the application is quitting
        """
        # No need to save the settings here as long as ArgosApplication.exit has been called.
        logger.info("Argos is about to quit")
        # QtWidgets.QMessageBox.warning(None, "Exit in progress", "We are quitting")


    def execute(self):
        """ Executes all main windows by starting the Qt main application
        """
        logger.info("Starting Argos event loop...")
        exitCode = self.qApplication.exec_()
        logger.info("Argos event loop finished with exit code: {}".format(exitCode))
        return exitCode

