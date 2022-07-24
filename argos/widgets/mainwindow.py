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

"""
    Main window functionality

"""


import base64
import cProfile
import logging
import os.path
import pstats
from functools import partial

import numpy as np

from argos.collect.collector import Collector
from argos.config.abstractcti import AbstractCti
from argos.config.configtreemodel import ConfigTreeModel
from argos.config.configtreeview import ConfigWidget
from argos.info import DEBUGGING, PROJECT_NAME, PROFILING, EXIT_CODE_RESTART
from argos.inspector.abstract import AbstractInspector, UpdateReason
from argos.inspector.errormsg import ErrorMsgInspector
from argos.inspector.selectionpane import InspectorSelectionPane
from argos.qt import Qt, QUrl, QtCore, QtGui, QtWidgets, QtSignal, QtSlot
from argos.qt.misc import getWidgetGeom, getWidgetState
from argos.reg.basereg import nameToIdentifier
from argos.reg.dialog import PluginsDialog
from argos.repo.iconfactory import RtiIconFactory
from argos.repo.registry import RtiRegistry
from argos.repo.repotreeview import RepoWidget
from argos.repo.testdata import createArgosTestData
from argos.utils.cls import check_class, check_is_a_sequence
from argos.utils.dirs import argosConfigDirectory, argosLogDirectory
from argos.utils.misc import string_to_identifier
from argos.utils.moduleinfo import versionStrToTuple
from argos.widgets.aboutdialog import AboutDialog
from argos.widgets.testwalkdialog import TestWalkDialog

logger = logging.getLogger(__name__)

# The main window inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201


class MainWindow(QtWidgets.QMainWindow):
    """ Main application window.
    """
    __numInstances = 0

    # Emitted when the inspector has changed.
    sigInspectorChanged = QtSignal(object)  # InspectorRegItem or None
    sigShowMessage = QtSignal(str) # Message to the user in the inspector-selection panel

    def __init__(self, argosApplication):
        """ Constructor
            :param reset: If true the persistent settings, such as column widths, are reset.
        """
        super(MainWindow, self).__init__()
        self._windowNumber = MainWindow.__numInstances # Used only for debugging
        MainWindow.__numInstances += 1

        if PROFILING:
            # Profiler that measures the drawing of the inspectors.
            self._profFileName = "inspectors.prof"

            logger.warning("Profiling is on for {}. This may cost a bit of CPU time.")
            self._profiler = cProfile.Profile()

        self.testWalkDialog = TestWalkDialog(mainWindow=self, parent=self)  # don't show yet

        self._collector = None
        self._inspector = ErrorMsgInspector(
            self._collector, "No inspector yet. Please select one from the menu.")
        self._inspector.sigShowMessage.connect(self.sigShowMessage)
        self._inspector.sigUpdated.connect(self.testWalkDialog.setTestResult)
        self._inspectorRegItem = None # The registered inspector item a InspectorRegItem)

        self._argosApplication = argosApplication
        self._configTreeModel = ConfigTreeModel()
        self._inspectorStates = {}  # keeps track of earlier inspector states
        self._currentTestName = None
        self._failedTests = []

        self.setDockNestingEnabled(False)
        self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.TopRightCorner, Qt.TopDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.BottomDockWidgetArea)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setUnifiedTitleAndToolBarOnMac(True)
        #self.setDocumentMode(True) # Look of tabs as Safari on OS-X (disabled, ugly)
        self.resize(1300, 700)  # Assumes minimal resolution of 1366 x 768

        # Move window to the center of the screen
        desktopRect = QtWidgets.QApplication.desktop().availableGeometry(self)
        center = desktopRect.center()
        self.move(round(center.x() - self.width () * 0.5), round(center.y() - self.height() * 0.5))

        self.__setupActions()
        self.__setupMenus()
        self.__setupViews()
        self.__setupDockWidgets()

        for detailsPane in self.repoWidget.detailDockPanes:
            detailsPane.sigUpdated.connect(self.testWalkDialog.setTestResult)


    def finalize(self):
        """ Is called before destruction (when closing).
            Can be used to clean-up resources.
        """
        logger.debug("Finalizing: {}".format(self))

        self.testWalkDialog.finalize()

        # Disconnect signals
        self.collector.sigContentsChanged.disconnect(self.collectorContentsChanged)
        self._configTreeModel.sigItemChanged.disconnect(self.configContentsChanged)
        self.sigInspectorChanged.disconnect(self.inspectorSelectionPane.updateFromInspectorRegItem)
        self.sigShowMessage.disconnect(self.inspectorSelectionPane.showMessage)
        self._collector.sigShowMessage.disconnect(self.sigShowMessage)
        self._inspector.sigShowMessage.disconnect(self.sigShowMessage)
        self._inspector.sigUpdated.disconnect(self.testWalkDialog.setTestResult)

        for detailsPane in self.repoWidget.detailDockPanes:
            detailsPane.sigUpdated.disconnect(self.testWalkDialog.setTestResult)

        if PROFILING:
            logger.info("Saving profiling information to {}"
                        .format(os.path.abspath(self._profFileName)))
            profStats = pstats.Stats(self._profiler)
            profStats.dump_stats(self._profFileName)

        self.inspector.finalize()


    def __setupViews(self):
        """ Creates the UI widgets.
        """
        self._collector = Collector(self.windowNumber)
        self._collector.sigShowMessage.connect(self.sigShowMessage)

        self.configWidget = ConfigWidget(self._configTreeModel)
        self.repoWidget = RepoWidget(self.argosApplication.repo, self.collector)

        # self._configTreeModel.insertItem(self.repoWidget.repoTreeView.config) # No configurable items yet

        # Define a central widget that will be the parent of the inspector widget.
        # We don't set the inspector directly as the central widget to retain the size when the
        # inspector is changed.
        self.mainWidget = QtWidgets.QWidget()
        self.mainLayout = QtWidgets.QVBoxLayout(self.mainWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.setCentralWidget(self.mainWidget)

        self.topPane = QtWidgets.QFrame()
        # self.topPane.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Raised)
        # self.topPane.setLineWidth(1)
        self.mainLayout.addWidget(self.topPane)

        self.topLayout = QtWidgets.QHBoxLayout(self.topPane)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.setSpacing(0)

        self.inspectorSelectionPane = InspectorSelectionPane(self.inspectorActionGroup)
        self.topLayout.addWidget(self.inspectorSelectionPane)
        self.sigInspectorChanged.connect(self.inspectorSelectionPane.updateFromInspectorRegItem)
        self.sigShowMessage.connect(self.inspectorSelectionPane.showMessage)

        showInspectorMenuAction = QtWidgets.QAction("ShowInspectorMenu", self,
            triggered=self.inspectorSelectionPane.menuButton.showMenu, checkable=False)
        showInspectorMenuAction.setShortcut("Ctrl+I")
        self.addAction(showInspectorMenuAction)

        self.wrapperWidget = QtWidgets.QWidget()
        self.mainLayout.addWidget(self.wrapperWidget)

        self.wrapperLayout = QtWidgets.QVBoxLayout(self.wrapperWidget)
        self.wrapperLayout.setContentsMargins(0, 0, 0, 0)
        self.wrapperLayout.setSpacing(0)
        self.wrapperLayout.addWidget(self.inspector)

        # Must be after setInspector since that already draws the inspector
        self.collector.sigContentsChanged.connect(self.collectorContentsChanged)
        self._configTreeModel.sigItemChanged.connect(self.configContentsChanged)

        # Populate table headers menu
        self.__addTableHeadersSubMenu("Data", self.repoWidget.repoTreeView)
        self.__addTableHeadersSubMenu("Settings", self.configWidget.configTreeView)
        self.__addTableHeadersSubMenu(
            "Properties", self.repoWidget.propertiesPane.table)
        self.__addTableHeadersSubMenu(
            "Attributes", self.repoWidget.attributesPane.table)


    def __addTableHeadersSubMenu(self, menuTitle, treeView):
        """ Adds a sub menu to the View | Table Headers menu with actions to show/hide columns
        """
        subMenu = self.tableHeadersMenu.addMenu(menuTitle)
        for action in treeView.getHeaderContextMenuActions():
            subMenu.addAction(action)


    def __setupActions(self):
        """ Creates actions that are always usable, even if they are not added to the main menu.

            Some actions are only added to the menu in debugging mode.
        """
        self.showTestWalkDialogAction = QtWidgets.QAction("Test Walk...", self)
        self.showTestWalkDialogAction.setToolTip("Shows test-walk dialog windows.")
        self.showTestWalkDialogAction.setShortcut("Ctrl+T")
        self.showTestWalkDialogAction.triggered.connect(self.showTestWalkDialog)
        self.addAction(self.showTestWalkDialogAction)

        # The action added to the menu in the repopulateWindowMenu method, which is called by
        # the ArgosApplication object every time a window is added or removed.
        self.activateWindowAction = QtWidgets.QAction("Window #{}".format(self.windowNumber), self)
        self.activateWindowAction.triggered.connect(self.activateAndRaise)
        self.activateWindowAction.setCheckable(True)
        #self.addAction(self.activateWindowAction)

        if self.windowNumber <= 9:
            self.activateWindowAction.setShortcut(QtGui.QKeySequence(
                "Alt+{}".format(self.windowNumber)))

        self.addTestDataAction = QtWidgets.QAction("Add Test Data", self)
        self.addTestDataAction.setToolTip("Add in-memory test data to the tree.")
        self.addTestDataAction.setShortcut("Meta+A")
        self.addTestDataAction.triggered.connect(self.addTestData)
        self.addAction(self.addTestDataAction)

        self.myTestAction = QtWidgets.QAction("My Test", self)
        self.myTestAction.setToolTip("Ad-hoc test procedure for debugging.")
        self.myTestAction.setShortcut("Meta+T")
        self.myTestAction.triggered.connect(self.myTest)
        self.addAction(self.myTestAction)


    def __setupMenus(self):
        """ Sets up the main menu.
        """
        if True:
            # Don't use self.menuBar(), on OS-X this is not shared across windows.
            # See: http://qt-project.org/doc/qt-4.8/qmenubar.html#details
            # And:http://qt-project.org/doc/qt-4.8/qmainwindow.html#menuBar
            menuBar = QtWidgets.QMenuBar() # Make a menu without parent.
            self.setMenuBar(menuBar)
        else:
            menuBar = self.menuBar()

        ### File Menu ###

        fileMenu = menuBar.addMenu("&File")

        fileMenu.addAction("&New Window", self.cloneWindow, QtGui.QKeySequence("Ctrl+N"))
        fileMenu.addAction("Close &Window", self.close, QtGui.QKeySequence.Close)

        fileMenu.addSeparator()

        action = fileMenu.addAction("Browse Directory...",
            lambda: self.openFiles(fileMode = QtWidgets.QFileDialog.Directory))
        action.setShortcut(QtGui.QKeySequence("Ctrl+B"))

        action = fileMenu.addAction("&Open Files...",
            lambda: self.openFiles(fileMode = QtWidgets.QFileDialog.ExistingFiles))
        action.setShortcut(QtGui.QKeySequence("Ctrl+O"))

        self.openAsMenu = fileMenu.addMenu("Open As")
        self.openAsMenu.aboutToShow.connect(self._repopulateOpenAsMenu)

        self.openRecentMenu = fileMenu.addMenu("Open Recent")
        self.openRecentMenu.aboutToShow.connect(self._repopulateOpenRecentMenu)

        fileMenu.addSeparator()

        fileMenu.addSeparator()
        fileMenu.addAction("E&xit", self.argosApplication.quit, 'Ctrl+Q')

        ### View Menu ###

        self.viewMenu = menuBar.addMenu("&View")

        self.inspectorActionGroup = self.__createInspectorActionGroup(self)
        for action in self.inspectorActionGroup.actions():
            self.viewMenu.addAction(action)

        self.viewMenu.addSeparator()
        self.panelsMenu = self.viewMenu.addMenu("&Panels")
        self.tableHeadersMenu = self.viewMenu.addMenu("&Table Headers")

        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.showTestWalkDialogAction)

        ### Config Menu ###

        self.configMenu = menuBar.addMenu("Configure")

        app = self.argosApplication
        action = self.configMenu.addAction("&File Format Plugins...",
            lambda: self.execPluginsDialog("File Formats", app.rtiRegistry))
        action.setShortcut(QtGui.QKeySequence("Ctrl+P"))

        action = self.configMenu.addAction("&Inspector Plugins...",
            lambda: self.execPluginsDialog("Inspectors", app.inspectorRegistry))

        self.configMenu.addSeparator()

        self.configMenu.addAction(
            "Show Config Files...",
            lambda: self.openInExternalApp(argosConfigDirectory()))

        ### Window Menu ###

        # Will be populated in repopulateWindowMenu
        self.windowMenu = menuBar.addMenu("&Window")

        ### Help Menu ###
        menuBar.addSeparator()
        helpMenu = menuBar.addMenu("&Help")
        helpMenu.addAction(
            "&Online Documentation...",
            lambda: self.openInWebBrowser("https://github.com/titusjan/argos#argos"))

        helpMenu.addSeparator()

        helpMenu.addAction(
            "Show Log Files...",
            lambda: self.openInExternalApp(argosLogDirectory()))

        helpMenu.addAction('&About...', self.about)

        if DEBUGGING:

            helpMenu.addSeparator()
            helpMenu.addAction(self.addTestDataAction)

            helpMenu.addAction(
                "Quick Walk &Current Node",
                lambda: self.testWalkDialog.walkCurrentRepoNode(False, False), "Meta+Q")
            helpMenu.addAction(
                "Walk &All Nodes",
                lambda: self.testWalkDialog.walkAllRepoNodes(True, True), "Meta+W")  # meta works on MacOs

            helpMenu.addSeparator()
            helpMenu.addAction(self.myTestAction)



    def __createInspectorActionGroup(self, parent):
        """ Creates an action group with 'set inspector' actions for all installed inspector.
        """
        actionGroup = QtWidgets.QActionGroup(parent)
        actionGroup.setExclusive(True)

        for item in self.argosApplication.inspectorRegistry.items:
            logger.debug("__createInspectorActionGroup item: {} {}".format(item.identifier, item._data))
            setAndDrawFn = partial(self.setAndDrawInspectorById, item.identifier)
            action = QtWidgets.QAction(item.name, self, triggered=setAndDrawFn, checkable=True)
            action.setData(item.identifier)
            if item.shortCut:
                try:
                    keySeq = QtGui.QKeySequence(item.shortCut.strip())
                except Exception as ex:
                    logger.warning("Unable to create shortcut from: '{}".format(item.shortCut))
                else:
                    action.setShortcut(QtGui.QKeySequence(keySeq))

            actionGroup.addAction(action)

        return actionGroup


    def __setupDockWidgets(self):
        """ Sets up the dock widgets. Must be called after the menu is setup.
        """
        #self.dockWidget(self.currentInspectorPane, "Current Inspector", Qt.LeftDockWidgetArea)

        self.dockWidget(self.repoWidget, "Data", Qt.LeftDockWidgetArea)
        self.dockWidget(self.collector, "Collector", Qt.BottomDockWidgetArea)
        # TODO: if the title == "Settings" it won't be added to the view menu (2020-03-29 On OS-X it seems to work now)
        self.dockWidget(self.configWidget, "Settings", Qt.RightDockWidgetArea)



    ##############
    # Properties #
    ##############

    @property
    def windowNumber(self):
        """ The instance number of this window.
        """
        return self._windowNumber

    @property
    def inspectorRegItem(self):
        """ The InspectorRegItem that has been selected. Contains an InspectorRegItem.
            Can be None (e.g. at start-up).
        """
        return self._inspectorRegItem

    @property
    def inspectorId(self):
        """ The ID of the inspector registry item that has been selected.
            E.g. ''. Can be None (e.g. at start-up).
        """
        return self._inspectorRegItem.identifier if self._inspectorRegItem else None

    @property
    def inspectorName(self):
        """ The name of the inspector registry item that has been selected.
            E.g. 'Table'. Can be None (e.g. at start-up).
        """
        return self._inspectorRegItem.name if self._inspectorRegItem else None

    @property
    def inspectorFullName(self):
        """ The full name of the inspector registry item that has been selected.
            E.g. 'Qt/Table'. Can be None (e.g. at start-up).
        """
        return self._inspectorRegItem.name if self._inspectorRegItem else None

    @property
    def inspector(self):
        """ The inspector widget of this window. Can be None (e.g. at start-up).
        """
        return self._inspector

    @property
    def collector(self):
        """ The collector widget of this window
        """
        return self._collector

    @property
    def argosApplication(self):
        """ The ArgosApplication to which this window belongs.
        """
        return self._argosApplication

    ###########
    # Methods #
    ###########


    def _repopulateOpenRecentMenu(self, *args, **kwargs):
        """ Clear the window menu and fills it with the actions of the actionGroup
        """
        logger.debug("Called _repopulateOpenRecentMenu")
        rtiIconFactory = RtiIconFactory.singleton()

        for action in self.openRecentMenu.actions():
            self.openRecentMenu.removeAction(action)

        # Count duplicate basename. These will be added with their full path.
        baseNameCount = {}
        for _timeStamp, fileName, _rtiRegName in self._argosApplication.getRecentFiles():
            _, baseName = os.path.split(fileName)
            if baseName in baseNameCount:
                baseNameCount[baseName] += 1
            else:
                baseNameCount[baseName] = 1

        # List returned by getRecentFiles is already sorted.
        for _timeStamp, fileName, rtiRegItemName in self._argosApplication.getRecentFiles():

            regItemId = nameToIdentifier(rtiRegItemName)
            rtiRegItem = self.argosApplication.rtiRegistry.getItemById(regItemId)

            # Bit of a hack to use a Directory RegItem, which is not in the registry.
            if rtiRegItem is None:
                directoryRtiRegItem = self.argosApplication.rtiRegistry.DIRECTORY_REG_ITEM
                if rtiRegItemName == 'Directory':
                    rtiRegItem = directoryRtiRegItem

            if rtiRegItem and not rtiRegItem.triedImport:
                rtiRegItem.tryImportClass()

            def createTrigger():
                "Function to create a closure with the regItem"
                _fileNames = [fileName] # keep reference in closure
                _rtiRegItem = rtiRegItem # keep reference in closure
                return lambda: self.openFiles(_fileNames, rtiRegItem=_rtiRegItem)

            dirName, baseName = os.path.split(fileName)
            fileLabel = fileName if baseNameCount[baseName] > 1 else baseName

            action = QtWidgets.QAction(fileLabel, self, enabled=True, triggered=createTrigger())
            action.setToolTip(fileName)
            if rtiRegItem is not None:
                action.setIcon(rtiRegItem.decoration)
            else:
                # Reserve space
                action.setIcon(rtiIconFactory.getIcon(RtiIconFactory.TRANSPARENT, False))

            self.openRecentMenu.addAction(action)


    def _repopulateOpenAsMenu(self, *args, **kwargs):
        """ Clear the window menu and fills it with the actions of the actionGroup
        """
        logger.debug("Called repopulateOpenAsMenu")

        for action in self.openAsMenu.actions():
            self.openAsMenu.removeAction(action)

        rtiRegistry = self.argosApplication.rtiRegistry
        for rtiRegItem in (rtiRegistry.items + rtiRegistry.extraItemsForOpenAsMenu()):
            if not rtiRegItem.triedImport:
                rtiRegItem.tryImportClass()

            def createTrigger():
                "Function to create a closure with the regItem"
                _rtiRegItem = rtiRegItem # keep reference in closure
                return lambda: self.openFiles(rtiRegItem=_rtiRegItem,
                                              fileMode = QtWidgets.QFileDialog.ExistingFiles,
                                              caption="Open {}".format(_rtiRegItem.name))

            action = QtWidgets.QAction("{}...".format(rtiRegItem.name), self,
                enabled=bool(rtiRegItem.successfullyImported),
                triggered=createTrigger(), icon=rtiRegItem.decoration)

            self.openAsMenu.addAction(action)


    def repopulateWindowMenu(self, actionGroup):
        """ Clear the window menu and fills it with the actions of the actionGroup
        """
        for action in self.windowMenu.actions():
            self.windowMenu.removeAction(action)

        for action in actionGroup.actions():
            self.windowMenu.addAction(action)


    def dockWidget(self, widget, title, area):
        """ Adds a widget as a docked widget.
            Returns the added dockWidget
        """
        assert widget.parent() is None, "Widget already has a parent"

        dockWidget = QtWidgets.QDockWidget(title, parent=self)
        # Use dock2 as name to reset at upgrade
        dockWidget.setObjectName("dock2_" + string_to_identifier(title)) # Use doc
        dockWidget.setWidget(widget)
        self.addDockWidget(area, dockWidget)

        self.panelsMenu.addAction(dockWidget.toggleViewAction())
        return dockWidget


    def updateWindowTitle(self):
        """ Updates the window title frm the window number, inspector, etc
            Also updates the Window Menu
        """
        title = "{} #{} | {}".format(self.inspectorName, self.windowNumber, PROJECT_NAME)

        # Display settings file name in title bar if it's not the default
        settingsFile = os.path.basename(self.argosApplication.settingsFile)
        if settingsFile != 'settings.json':
            title = "{} -- {}".format(title, settingsFile)

        self.setWindowTitle(title)
        #self.activateWindowAction.setText("{} window".format(self.inspectorName, self.windowNumber))
        self.activateWindowAction.setText("{} window".format(self.inspectorName))


    def getInspectorActionById(self, identifier):
        """ Sets the inspector and draw the contents
            Triggers the corresponding action so that it is checked in the menus.
        """
        for action in self.inspectorActionGroup.actions():
            if action.data() == identifier:
                return action
        raise KeyError("No action found with ID: {!r}".format(identifier))


    def setAndDrawInspectorById(self, identifier):
        """ Sets the inspector and draw the contents.

            Does NOT trigger any actions, so the check marks in the menus are not updated. To
            achieve this, the user must update the actions by hand (or call
            getInspectorActionById(identifier).trigger() instead).
        """
        self.setInspectorById(identifier)

        # Show dialog box if import was unsuccessful.
        regItem = self.inspectorRegItem
        if regItem and not regItem.successfullyImported:
            msg = "Unable to import {} inspector.\n{}".format(regItem.identifier, regItem.exception)
            QtWidgets.QMessageBox.warning(self, "Warning", msg)
            logger.warning(msg)

        self.drawInspectorContents(reason=UpdateReason.INSPECTOR_CHANGED)


    def setInspectorById(self, identifier):
        """ Sets the central inspector widget given a inspector ID.

            If identifier is None, the inspector will be unset. Otherwise it will lookup the
            inspector class in the registry. It will raise a KeyError if the ID is not found there.

            It will do an import of the inspector code if it's loaded for the first time. If the
            the inspector class cannot be imported a warning is logged and the inspector is unset.

            NOTE: does not draw the new inspector, this is the responsibility of the caller.
            Also, the corresponding action is not triggered.

            Emits the sigInspectorChanged(self.inspectorRegItem)
        """
        logger.debug("Setting inspector: {}".format(identifier))

        # Use the identifier to find a registered inspector and set self.inspectorRegItem.
        # Then create an inspector object from it.

        oldInspectorRegItem = self.inspectorRegItem
        oldInspector = self.inspector

        inspector = None
        errMsg = None

        if not identifier:
            errMsg = "No inspector selected. Please select one from menu."
            self._inspectorRegItem = None
        else:
            inspectorRegistry = self.argosApplication.inspectorRegistry
            inspectorRegItem = inspectorRegistry.getItemById(identifier)  #

            self._inspectorRegItem = inspectorRegItem
            if inspectorRegItem is None:
                errMsg = "No {!r} inspector found. Please select one from menu.".format(identifier)
            else:
                try:
                    inspector = inspectorRegItem.create(self.collector, tryImport=True)
                except ImportError as ex:
                    # Only log the error. No dialog box or user interaction here because this
                    # function may be called at startup.
                    errMsg = "Unable to create {!r} inspector because {}"\
                        .format(inspectorRegItem.identifier, ex)
                    logger.warning(errMsg, exc_info=DEBUGGING)
                    self.getInspectorActionById(identifier).setEnabled(False)

        ###### Set self.inspector ######

        check_class(inspector, AbstractInspector, allow_none=True)

        logger.debug("Disabling updates.")
        self.setUpdatesEnabled(False)
        try:
            # Delete old inspector
            self._storeInspectorState(oldInspectorRegItem, oldInspector)

            oldInspector.sigShowMessage.disconnect(self.sigShowMessage)
            oldInspector.sigUpdated.disconnect(self.testWalkDialog.setTestResult)
            oldInspector.finalize()
            self.wrapperLayout.removeWidget(oldInspector)
            oldInspector.deleteLater()

            # Set new inspector, update collector widgets and the config tree
            oldBlockState = self.collector.blockSignals(True)
            try:
                if inspector is None:
                    logger.warning(errMsg)
                    self._inspector = ErrorMsgInspector(self._collector, errMsg)
                    self.collector.clearAndSetComboBoxes([])
                else:
                    assert not errMsg, "Unexpected error message: {}".format(errMsg)
                    self._inspector = inspector
                    # Add and apply config values to the inspector
                    key = self.inspectorRegItem.identifier
                    cfg = self._inspectorStates.get(key, {})
                    logger.debug("Setting inspector settings from : {}".format(cfg))
                    self.inspector.config.unmarshall(cfg)
                    self._configTreeModel.setInvisibleRootItem(self.inspector.config)
                    self.configWidget.configTreeView.expandBranch()
                    self.collector.clearAndSetComboBoxes(self.inspector.axesNames())

                self._inspector.sigShowMessage.connect(self.sigShowMessage)
                self._inspector.sigUpdated.connect(self.testWalkDialog.setTestResult)
                self.wrapperLayout.addWidget(self.inspector)
            finally:
                self.collector.blockSignals(oldBlockState)
        finally:
            logger.debug("Enabling updates.")
            self.setUpdatesEnabled(True)

            self.updateWindowTitle()

            logger.debug("Emitting sigInspectorChanged({})".format(self.inspectorRegItem))
            self.sigInspectorChanged.emit(self.inspectorRegItem)


    def _storeInspectorState(self, inspectorRegItem, inspector):
        """ Store the settings values for the current inspector in a local dictionary.
            This dictionary is later used to store value for persistence.

            This function must be called after the inspector was drawn because that may update
            some derived config values (e.g. ranges)
        """
        if inspectorRegItem and inspector:
            key = inspectorRegItem.identifier
            logger.debug("_updateInspectorState: {} {}".format(key, type(inspector)))
            self._inspectorStates[key] = inspector.config.marshall()
        else:
            logger.debug("_updateInspectorState: no inspector")


    @QtSlot()
    def execPluginsDialog(self, label, registry):
        """ Shows the plugins dialog with the registered plugins
        """
        pluginsDialog = PluginsDialog(label, registry, parent=self)
        pluginsDialog.exec_()
        pluginsDialog.deleteLater()

        if pluginsDialog.result() == PluginsDialog.Accepted:
            logger.info("Accepted changes to {} registry.".format(label))

            logger.critical("Closing all windows and restarting eventloop")
            self.argosApplication.exit(EXIT_CODE_RESTART)
        else:
            logger.info("Cancelled changes to {} registry.".format(label))



    @QtSlot(str)
    def collectorContentsChanged(self, reason):
        """ Slot that updates the UI whenever the contents of the collector has changed.
        """
        logger.debug("collectorContentsChanged()")
        self.drawInspectorContents(reason=reason)


    @QtSlot(AbstractCti)
    def configContentsChanged(self, configTreeItem):
        """ Slot is called when an item has been changed by setData of the ConfigTreeModel.
            Will draw the window contents.
        """
        logger.debug("configContentsChanged: {}".format(configTreeItem))
        self.drawInspectorContents(reason=UpdateReason.CONFIG_CHANGED,
                                   origin=configTreeItem)

    def showMessage(self, msg):
        """ Shows a message to the user in the panel above the inspector
        """
        self.inspectorSelectionPane.showMessage(msg)


    def drawInspectorContents(self, reason, origin=None):
        """ Draws all contents of this window's inspector.
            The reason and origin parameters are passed on to the inspector's updateContents method.

            :param reason: string describing the reason for the redraw.
                Should preferably be one of the UpdateReason enumeration class, but new values may
                be used (which are then ignored by existing inspectors).
            :param origin: object with extra info on the reason
        """
        logger.debug("")
        logger.debug("-------- Drawing inspector of window: {} --------".format(self.windowTitle()))
        if PROFILING:
            self._profiler.enable()

        #self.showMessage(reason)
        self.showMessage('')  # clear message

        self.inspector.updateContents(reason=reason, initiator=origin)

        if PROFILING:
            self._profiler.disable()
        logger.debug("Finished draw inspector.\n")


    # TODO: to repotreemodel? Note that the functionality will be common to selectors.
    @QtSlot()
    def openFiles(self, fileNames=None, rtiRegItem=None, caption=None, fileMode=None):
        """ Lets the user select on or more files and opens it.

            :param fileNames: If None an open-file dialog allows the user to select files,
                otherwise the files are opened directly.
            :param rtiRegItem: Open the files as this type of registered RTI. None=autodetect.
            :param caption: Optional caption for the file dialog.
            :param fileMode: is passed to the file dialog.
            :rtype fileMode: QtWidgets.QFileDialog.FileMode constant
        """
        check_is_a_sequence(fileNames, allow_none=True)
        if fileNames is None:
            dialog = QtWidgets.QFileDialog(self, caption=caption)

            if rtiRegItem is None:
                nameFilter = 'All files (*);;' # Default show all files.
                nameFilter += self.argosApplication.rtiRegistry.getFileDialogFilter()
                if fileMode == QtWidgets.QFileDialog.Directory:
                    rtiRegItemName = 'Directory'
                else:
                    rtiRegItemName = ''
            else:
                nameFilter = rtiRegItem.getFileDialogFilter()
                nameFilter += ';;All files (*)'
                rtiRegItemName = rtiRegItem.name
            dialog.setNameFilter(nameFilter)

            if fileMode:
                dialog.setFileMode(fileMode)

            if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
                fileNames = dialog.selectedFiles()
            else:
                fileNames = []

            # Only add files that were added via the dialog box (not via the command line).
            self._argosApplication.addToRecentFiles(fileNames, rtiRegItemName)

        fileRootIndex = None

        logger.debug("Adding files: {}".format(fileNames))
        for fileName in fileNames:
            fileRootIndex = self.argosApplication.repo.loadFile(fileName, rtiRegItem=rtiRegItem)

        if len(fileNames) == 1: # Only expand and open the file if the user selected one.
            logger.debug("Opening file: {}".format(fileNames[0]))
            self.repoWidget.repoTreeView.setExpanded(fileRootIndex, True)

        # Select last opened file
        if fileRootIndex is not None:
            self.repoWidget.repoTreeView.setCurrentIndex(fileRootIndex)


    def selectRtiByPath(self, path):
        """ Selects a repository tree item given a path, expanding nodes if along the way if needed.

            Returns (item, index) if the path was selected successfully, else raises an IndexError.
        """
        lastItem, lastIndex = self.repoWidget.repoTreeView.expandPath(path)
        self.repoWidget.repoTreeView.setCurrentIndex(lastIndex)
        return lastItem, lastIndex


    def trySelectRtiByPath(self, path):
        """ Selects a repository tree item given a path, expanding nodes if along the way if needed.

            Returns (item, index) if the path was selected successfully, else a warning is logged
            and (None, None) is returned.
        """
        try:
            logger.debug("Trying to select: {}".format(path))
            lastItem, lastIndex = self.repoWidget.repoTreeView.expandPath(path)
            self.repoWidget.repoTreeView.setCurrentIndex(lastIndex)
            self.repoWidget.repoTreeView.setFocus()
            return lastItem, lastIndex
        except Exception as ex:
            logger.warning("Unable to select {!r} because: {}".format(path, ex))
            if DEBUGGING:
                raise
            return None, None


    def openInWebBrowser(self, url):
        """ Opens url or file in an external documentation.

            Regular URLs are opened in the web browser, Local URLs are opened in the application
            that is used to open that type of file by default.
        """
        try:
            logger.debug("Opening URL: {}".format(url))
            qUrl = QUrl(url)
            QtGui.QDesktopServices.openUrl(qUrl)
        except Exception as ex:
            msg = "Unable to open URL {}. \n\nDetails: {}".format(url, ex)
            QtWidgets.QMessageBox.warning(self, "Warning", msg)
            logger.error(msg.replace('\n', ' '))


    def openInExternalApp(self, fileName):
        """ Opens url or file in an external documentation.

            Regular URLs are opened in the web browser, Local URLs are opened in the application
            that is used to open that type of file by default.
        """
        try:
            logger.debug("Opening URL: {}".format(fileName))
            if not os.path.exists(fileName):
                raise OSError("File doesn't exist.")
            url = QUrl.fromLocalFile(fileName)
            QtGui.QDesktopServices.openUrl(url)
        except Exception as ex:
            msg = "Unable to open file '{}'. \n\nDetails: {}".format(fileName, ex)
            QtWidgets.QMessageBox.warning(self, "Warning", msg)
            logger.error(msg.strip('\n'))


    def marshall(self):
        """ Returns a dictionary to save in the persistent settings
        """
        self._storeInspectorState(self.inspectorRegItem, self.inspector)

        twLayoutCfg, twCfg = self.testWalkDialog.marshall()

        layoutCfg = dict(
            repoWidget = self.repoWidget.marshall(),
            configTreeHeaders =  self.configWidget.configTreeView.marshall(),
            collectorHeaders = self.collector.tree.marshall(),
            winGeom = base64.b64encode(getWidgetGeom(self)).decode('ascii'),
            winState = base64.b64encode(getWidgetState(self)).decode('ascii'),
            testWalkDialog = twLayoutCfg,
        )

        cfg = dict(
            configWidget = self.configWidget.marshall(),
            curInspector = self.inspectorRegItem.identifier if self.inspectorRegItem else '',
            inspectors = self._inspectorStates,
            testWalkDialog = twCfg,
            layout = layoutCfg,
        )
        return cfg


    def unmarshall(self, cfg):
        """ Initializes itself from a config dict form the persistent settings.
        """
        self.configWidget.unmarshall(cfg.get('configWidget', {}))

        self._inspectorStates = cfg.get('inspectors', {})

        curInspector = cfg.get('curInspector')
        if curInspector:
            try:
                logger.debug("Setting inspector to: {}".format(curInspector))
                self.setInspectorById(curInspector)
            except KeyError as ex:
                logger.warning("No inspector with ID {!r}.: {}".format(curInspector, ex))

        layoutCfg = cfg.get('layout', {})

        self.repoWidget.unmarshall(layoutCfg.get('repoWidget', {}))
        self.configWidget.configTreeView.unmarshall(layoutCfg.get('configTreeHeaders', ''))
        self.collector.tree.unmarshall(layoutCfg.get('collectorHeaders', ''))

        self.testWalkDialog.unmarshall(layoutCfg.get('testWalkDialog', {}),
                                       cfg.get('testWalkDialog', {}))

        if 'winGeom' in layoutCfg:
            self.restoreGeometry(base64.b64decode(layoutCfg['winGeom']))
        if 'winState' in layoutCfg:
            self.restoreState(base64.b64decode(layoutCfg['winState']))



    @QtSlot()
    def cloneWindow(self):
        """ Opens a new window with the same inspector as the current window.
        """
        newWindow = self.argosApplication.addNewMainWindow(
            cfg=self.marshall(), inspectorFullName=self.inspectorRegItem.name)

        # Select the current item in the new window.
        currentItem, _currentIndex = self.repoWidget.repoTreeView.getCurrentItem()
        if currentItem:
            newWindow.trySelectRtiByPath(currentItem.nodePath)

        # Move the new window 24 pixels to the bottom right and raise it to the front.
        newGeomRect = newWindow.geometry()
        logger.debug("newGeomRect: x={}".format(newGeomRect.x()))
        newGeomRect.moveTo(newGeomRect.x() + 24, newGeomRect.y() + 24)

        newWindow.setGeometry(newGeomRect)
        logger.debug("newGeomRect: x={}".format(newGeomRect.x()))

        newWindow.raise_()


    @QtSlot()
    def activateAndRaise(self):
        """ Activates and raises the window.
        """
        logger.debug("Activate and raising window: {}".format(self.windowNumber))
        self.activateWindow()
        self.raise_()


    def event(self, ev):
        """ Detects the WindowActivate event. Pass all event through to the super class.
        """
        if ev.type() == QtCore.QEvent.WindowActivate:
            logger.debug("Window activated: {}".format(self.windowNumber))
            self.activateWindowAction.setChecked(True)

        return super(MainWindow, self).event(ev);


    def closeEvent(self, event):
        """ Called when closing this window.
        """
        logger.debug("closeEvent")

        # Save settings must be called here, at the point that there is still a windows open.
        # We can't use the QApplication.aboutToQuit signal because at that point the windows have
        # been closed
        self.argosApplication.saveSettingsIfLastWindow()
        self.finalize()
        self.argosApplication.removeMainWindow(self)
        event.accept()
        logger.debug("closeEvent accepted")


    @QtSlot()
    def about(self):
        """ Shows the about message window.
        """
        aboutDialog = AboutDialog(parent=self)
        aboutDialog.show()
        aboutDialog.addDependencyInfo()


    def addTestData(self):
        """ Adds test data to the repository
        """
        logger.info("Adding test data to the repository.")
        self.argosApplication.repo.insertItem(createArgosTestData())


    def showTestWalkDialog(self):
        """ Shows the test-walk dialog box
        """
        self.testWalkDialog.show()
        self.testWalkDialog.raise_()


    @QtSlot()
    def myTest(self):
        """ Function for small ad-hoc tests that can be called from the menu.
        """
        logger.info("--------- myTest function called --------------------")

        logger.info("--------- myTest function done --------------------")


