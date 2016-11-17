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

from __future__ import absolute_import, division, print_function

import sys
from functools import partial

from libargos.collect.collector import Collector
from libargos.config.abstractcti import ctiDumps, ctiLoads
from libargos.config.abstractcti import AbstractCti
from libargos.config.configtreemodel import ConfigTreeModel
from libargos.config.configtreeview import ConfigTreeView
from libargos.info import DEBUGGING, PROJECT_NAME
from libargos.inspector.abstract import AbstractInspector, UpdateReason
from libargos.inspector.dialog import OpenInspectorDialog
from libargos.inspector.registry import InspectorRegItem
from libargos.inspector.selectionpane import InspectorSelectionPane, addInspectorActionsToMenu
from libargos.qt import Qt, QtCore, QtGui, QtWidgets, QtSignal, QtSlot

from libargos.repo.detailplugins.attr import AttributesPane
from libargos.repo.detailplugins.dim import DimensionsPane
from libargos.repo.detailplugins.prop import PropertiesPane
from libargos.repo.repotreeview import RepoTreeView
from libargos.repo.testdata import createArgosTestData
from libargos.utils.cls import check_class
from libargos.utils.misc import string_to_identifier
from libargos.widgets.aboutdialog import AboutDialog
from libargos.widgets.constants import CENTRAL_MARGIN, CENTRAL_SPACING
from libargos.widgets.pluginsdialog import PluginsDialog
import logging


logger = logging.getLogger(__name__)

# The main window inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201


class MainWindow(QtWidgets.QMainWindow):
    """ Main application window.
    """
    __numInstances = 0

    # Emitted when the inspector has changed.
    sigInspectorChanged = QtSignal(InspectorRegItem)

    def __init__(self, argosApplication):
        """ Constructor
            :param reset: If true the persistent settings, such as column widths, are reset.
        """
        super(MainWindow, self).__init__()
        self._windowNumber = MainWindow.__numInstances # Used only for debugging
        MainWindow.__numInstances += 1

        self._collector = None
        self._inspector = None
        self._inspectorRegItem = None # The registered inspector item a InspectorRegItem)

        self._detailDockWidgets = []
        self._argosApplication = argosApplication
        self._configTreeModel = ConfigTreeModel()
        self._inspectorsNonDefaults = {}  # non-default values for all used plugins

        self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.TopRightCorner, Qt.TopDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setUnifiedTitleAndToolBarOnMac(True)
        #self.setDocumentMode(True) # Look of tabs as Safari on OS-X (disabled, ugly)
        self.resize(1300, 700)  # Assumes minimal resolution of 1366 x 768
        self.setWindowTitle(self.constructWindowTitle())

        self.__setupViews()
        self.__setupMenus()
        self.__setupDockWidgets()


    def finalize(self):
        """ Is called before destruction (when closing).
            Can be used to clean-up resources.
        """
        logger.debug("Finalizing: {}".format(self))

        # Disconnect signals
        self.collector.sigContentsChanged.disconnect(self.collectorContentsChanged)
        self._configTreeModel.sigItemChanged.disconnect(self.configContentsChanged)
        self.sigInspectorChanged.disconnect(self.inspectorSelectionPane.updateFromInspectorRegItem)
        self.customContextMenuRequested.disconnect(self.showContextMenu)


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
        return self._inspectorRegItem.fullName if self._inspectorRegItem else None

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


    def __setupViews(self):
        """ Creates the UI widgets.
        """
        self._collector = Collector(self.windowNumber)
        self.configTreeView = ConfigTreeView(self._configTreeModel)
        self.repoTreeView = RepoTreeView(self.argosApplication.repo, self.collector)
        self._configTreeModel.insertItem(self.repoTreeView.config)

        # Define a central widget that will be the parent of the inspector widget.
        # We don't set the inspector directly as the central widget to retain the size when the
        # inspector is changed.
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(CENTRAL_MARGIN, CENTRAL_MARGIN, CENTRAL_MARGIN, CENTRAL_MARGIN)
        layout.setSpacing(CENTRAL_SPACING)
        self.setCentralWidget(widget)

        # Must be after setInspector since that already draws the inspector
        self.collector.sigContentsChanged.connect(self.collectorContentsChanged)
        self._configTreeModel.sigItemChanged.connect(self.configContentsChanged)


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

        action = fileMenu.addAction("&New Window...", self.cloneWindow)
        action.setShortcut(QtGui.QKeySequence("Ctrl+N")) # TODO. Should open inspector selection window

        fileMenu.addSeparator()

        action = fileMenu.addAction("Browse Directory...",
            lambda: self.openFiles(fileMode = QtWidgets.QFileDialog.Directory))
        action.setShortcut(QtGui.QKeySequence("Ctrl+B"))

        action = fileMenu.addAction("&Open Files...",
            lambda: self.openFiles(fileMode = QtWidgets.QFileDialog.ExistingFiles))
        action.setShortcut(QtGui.QKeySequence("Ctrl+O"))

        openAsMenu = fileMenu.addMenu("Open As")
        for rtiRegItem in self.argosApplication.rtiRegistry.items:
            #rtiRegItem.tryImportClass()
            def createTrigger():
                "Function to create a closure with the regItem"
                _rtiRegItem = rtiRegItem # keep reference in closure
                return lambda: self.openFiles(rtiRegItem=_rtiRegItem,
                                              fileMode = QtWidgets.QFileDialog.ExistingFiles,
                                              caption="Open {}".format(_rtiRegItem.name))

            action = QtWidgets.QAction("{}...".format(rtiRegItem.name), self,
                enabled=True, # Since this is only executed at start-up, it must be static
                #enabled=bool(rtiRegItem.successfullyImported), # TODO: make this work?
                triggered=createTrigger())
            openAsMenu.addAction(action)

        for action in self.repoTreeView.topLevelItemActionGroup.actions():
            fileMenu.addAction(action)

        for action in self.repoTreeView.currentItemActionGroup.actions():
            fileMenu.addAction(action)

        fileMenu.addSeparator()
        fileMenu.addAction("Close &Window", self.close, QtGui.QKeySequence.Close)
        fileMenu.addAction("E&xit", self.argosApplication.closeAllWindows, QtGui.QKeySequence.Quit)

        ### View Menu ###
        self.viewMenu = menuBar.addMenu("&View")
        action = self.viewMenu.addAction("Installed &Plugins...", self.execPluginsDialog)
        action.setShortcut(QtGui.QKeySequence("Ctrl+P"))
        self.viewMenu.addSeparator()

        ### Inspector Menu ###
        self.execInspectorDialogAction = QtWidgets.QAction("&Browse Inspectors...", self,
                                                       triggered=self.execInspectorDialog)
        self.execInspectorDialogAction.setShortcut(QtGui.QKeySequence("Ctrl+i"))

        self.inspectorActionGroup = self.__createInspectorActionGroup(self)
        self.inspectorMenu = QtWidgets.QMenu("Inspector", parent=self)
        addInspectorActionsToMenu(self.inspectorMenu, self.execInspectorDialogAction,
                                  self.inspectorActionGroup)
        menuBar.addMenu(self.inspectorMenu)


        ### Help Menu ###
        menuBar.addSeparator()
        helpMenu = menuBar.addMenu("&Help")
        helpMenu.addAction('&About...', self.about)

        helpMenu.addSeparator()
        helpMenu.addAction("&Test", self.myTest, "Alt+T")
        helpMenu.addAction("Add Test Data", self.addTestData, "Alt+A")


        ### Context menu ###

        # Note that the dock-widgets have a Qt.PreventContextMenu context menu policy.
        # Therefor the context menu is only shown in the center widget.
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)


    def __createInspectorActionGroup(self, parent):
        """ Creates an action group with 'set inspector' actions for all installed inspector.
        """
        actionGroup = QtWidgets.QActionGroup(parent)
        actionGroup.setExclusive(True)

        sortedItems = sorted(self.argosApplication.inspectorRegistry.items,
                             key=lambda item: item.identifier)
        shortCutNr = 1
        for item in sortedItems:
            logger.debug("item: {}".format(item.identifier))
            setAndDrawFn = partial(self.setAndDrawInspectorById, item.identifier)
            action = QtWidgets.QAction(item.name, self, triggered=setAndDrawFn, checkable=True)
            action.setData(item.identifier)
            if shortCutNr <= 9 and "debug" not in item.identifier: # TODO: make configurable by the user
                action.setShortcut(QtGui.QKeySequence("Ctrl+{}".format(shortCutNr)))
                shortCutNr += 1

            actionGroup.addAction(action)

        return actionGroup


    def __setupDockWidgets(self):
        """ Sets up the dock widgets. Must be called after the menu is setup.
        """
        #self.dockWidget(self.currentInspectorPane, "Current Inspector", Qt.LeftDockWidgetArea)

        self.inspectorSelectionPane = InspectorSelectionPane(self.execInspectorDialogAction,
                                                             self.inspectorActionGroup)
        self.sigInspectorChanged.connect(self.inspectorSelectionPane.updateFromInspectorRegItem)
        self.dockWidget(self.inspectorSelectionPane, "Current Inspector",
                        area=Qt.LeftDockWidgetArea)

        self.dockWidget(self.repoTreeView, "Data Repository", Qt.LeftDockWidgetArea)
        self.dockWidget(self.collector, "Data Collector", Qt.TopDockWidgetArea)
        # TODO: if the title == "Settings" it won't be added to the view menu.
        self.dockWidget(self.configTreeView, "Application Settings", Qt.RightDockWidgetArea)

        self.viewMenu.addSeparator()

        propertiesPane = PropertiesPane(self.repoTreeView)
        self.dockDetailPane(propertiesPane, area=Qt.LeftDockWidgetArea)

        attributesPane = AttributesPane(self.repoTreeView)
        self.dockDetailPane(attributesPane, area=Qt.LeftDockWidgetArea)

        dimensionsPane = DimensionsPane(self.repoTreeView)
        self.dockDetailPane(dimensionsPane, area=Qt.LeftDockWidgetArea)

        # Add am extra separator on mac because OS-X adds an 'Enter Full Screen' item
        if sys.platform.startswith('darwin'):
            self.viewMenu.addSeparator()


    # -- End of setup_methods --

    def showContextMenu(self, pos):
        """ Shows the context menu at position pos.
        """
        contextMenu = QtWidgets.QMenu()
        addInspectorActionsToMenu(contextMenu, self.execInspectorDialogAction,
                                  self.inspectorActionGroup)
        contextMenu.exec_(self.mapToGlobal(pos))


    def dockWidget(self, widget, title, area):
        """ Adds a widget as a docked widget.
            Returns the added dockWidget
        """
        assert widget.parent() is None, "Widget already has a parent"

        dockWidget = QtWidgets.QDockWidget(title, parent=self)
        dockWidget.setObjectName("dock_" + string_to_identifier(title))
        dockWidget.setWidget(widget)

        # Prevent parent context menu (with e.g. 'set inspector" option) to be displayed.
        dockWidget.setContextMenuPolicy(Qt.PreventContextMenu)

        self.addDockWidget(area, dockWidget)
        self.viewMenu.addAction(dockWidget.toggleViewAction())
        return dockWidget


    def dockDetailPane(self, detailPane, title=None, area=None):
        """ Creates a dockWidget and add the detailPane with a default title.
            By default the detail widget is added to the Qt.LeftDockWidgetArea.
        """
        title = detailPane.classLabel() if title is None else title
        area = Qt.LeftDockWidgetArea if area is None else area
        dockWidget = self.dockWidget(detailPane, title, area)
        # TODO: undockDetailPane to disconnect
        dockWidget.visibilityChanged.connect(detailPane.dockVisibilityChanged)
        if len(self._detailDockWidgets) > 0:
            self.tabifyDockWidget(self._detailDockWidgets[-1], dockWidget)
        self._detailDockWidgets.append(dockWidget)
        return dockWidget


    def constructWindowTitle(self):
        """ Constructs the window title given the current inspector and profile.
        """
        return "{} #{} | {}-{}".format(self.inspectorName, self.windowNumber,
                                       PROJECT_NAME, self.argosApplication.profile)

    @QtSlot()
    def execInspectorDialog(self):
        """ Opens the inspector dialog box to let the user change the current inspector.
        """
        dialog = OpenInspectorDialog(self.argosApplication.inspectorRegistry, parent=self)
        dialog.setCurrentInspectorRegItem(self.inspectorRegItem)
        dialog.exec_()
        if dialog.result():
            inspectorRegItem = dialog.getCurrentInspectorRegItem()
            if inspectorRegItem is not None:
                self.getInspectorActionById(inspectorRegItem.identifier).trigger()


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
            logger.warn(msg)

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
        logger.info("Setting inspector: {}".format(identifier))

        # Use the identifier to find a registered inspector and set self.inspectorRegItem.
        # Then create an inspector object from it.

        oldInspectorRegItem = self.inspectorRegItem
        oldInspector = self.inspector

        if not identifier:
            inspector = None
            self._inspectorRegItem = None
        else:
            inspectorRegistry = self.argosApplication.inspectorRegistry
            inspectorRegItem = inspectorRegistry.getItemById(identifier)

            self._inspectorRegItem = inspectorRegItem
            if inspectorRegItem is None:
                inspector = None
            else:
                try:
                    inspector = inspectorRegItem.create(self.collector, tryImport=True)
                except ImportError as ex:
                    # Only log the error. No dialog box or user interaction here because this
                    # function may be called at startup.
                    logger.exception("Clearing inspector. Unable to create {!r} because {}"
                                     .format(inspectorRegItem.identifier, ex))
                    inspector = None
                    self.getInspectorActionById(identifier).setEnabled(False)

                    if DEBUGGING:
                        raise

        ######################
        # Set self.inspector #
        ######################

        check_class(inspector, AbstractInspector, allow_none=True)

        logger.debug("Disabling updates.")
        self.setUpdatesEnabled(False)
        try:
            centralLayout = self.centralWidget().layout()

            # Delete old inspector
            if oldInspector is None: # can be None at start-up
                oldConfigPosition = None
            else:
                self._updateNonDefaultsForInspector(oldInspectorRegItem, oldInspector)

                # Remove old inspector configuration from tree
                oldConfigPosition = oldInspector.config.childNumber()
                configPath = oldInspector.config.nodePath
                _, oldConfigIndex = self._configTreeModel.findItemAndIndexPath(configPath)[-1]
                self._configTreeModel.deleteItemAtIndex(oldConfigIndex)

                oldInspector.finalize() # TODO: before removing config
                centralLayout.removeWidget(oldInspector)
                oldInspector.deleteLater()

            # Set new inspector
            self._inspector = inspector

            # Update collector widgets and the config tree
            oldBlockState = self.collector.blockSignals(True)
            try:
                if self.inspector is None:
                    self.collector.clearAndSetComboBoxes([])
                else:
                    # Add and apply config values to the inspector
                    key = self.inspectorRegItem.identifier
                    nonDefaults = self._inspectorsNonDefaults.get(key, {})
                    logger.debug("Setting non defaults: {}".format(nonDefaults))
                    self.inspector.config.setValuesFromDict(nonDefaults)
                    self._configTreeModel.insertItem(self.inspector.config, oldConfigPosition)
                    self.configTreeView.expandBranch()
                    self.collector.clearAndSetComboBoxes(self.inspector.axesNames())
                    centralLayout.addWidget(self.inspector)
            finally:
                self.collector.blockSignals(oldBlockState)
        finally:
            logger.debug("Enabling updates.")
            self.setUpdatesEnabled(True)

            self.setWindowTitle(self.constructWindowTitle())

            logger.debug("Emitting sigInspectorChanged({})".format(self.inspectorRegItem))
            self.sigInspectorChanged.emit(self.inspectorRegItem)




    def _updateNonDefaultsForInspector(self, inspectorRegItem, inspector):
        """ Store the (non-default) config values for the current inspector in a local dictionary.
            This dictionary is later used to store value for persistence.

            This function must be called after the inspector was drawn because that may update
            some derived config values (e.g. ranges)
        """
        if inspectorRegItem and inspector:
            key = inspectorRegItem.identifier
            logger.debug("_updateNonDefaultsForInspector: {} {}"
                         .format(key, type(inspector)))
            self._inspectorsNonDefaults[key] = inspector.config.getNonDefaultsDict()
        else:
            logger.debug("_updateNonDefaultsForInspector: no inspector")


    @QtSlot()
    def execPluginsDialog(self):
        """ Shows the plugins dialog with the registered plugins
        """
        pluginsDialog = PluginsDialog(parent=self,
                                inspectorRegistry=self.argosApplication.inspectorRegistry,
                                rtiRegistry=self.argosApplication.rtiRegistry)
        pluginsDialog.exec_()


    @QtSlot()
    def collectorContentsChanged(self):
        """ Slot that updates the UI whenever the contents of the collector has changed.
        """
        logger.debug("collectorContentsChanged()")
        self.drawInspectorContents(reason=UpdateReason.COLLECTOR_CHANGED)


    @QtSlot(AbstractCti)
    def configContentsChanged(self, configTreeItem):
        """ Slot is called when an item has been changed by setData of the ConfigTreeModel.
            Will draw the window contents.
        """
        logger.debug("configContentsChanged: {}".format(configTreeItem))
        self.drawInspectorContents(reason=UpdateReason.CONFIG_CHANGED,
                                   origin=configTreeItem)


    def drawInspectorContents(self, reason, origin=None):
        """ Draws all contents of this window's inspector.
            The reason and origin parameters are passed on to the inspector's updateContents method.

            :param reason: string describing the reason for the redraw.
                Should preferably be one of the UpdateReason enumeration class, but new values may
                be used (which are then ignored by existing inspectors).
            :param origin: object with extra infor on the reason
        """
        logger.debug("")
        logger.debug("-------- Drawing inspector of window: {} --------".format(self.windowTitle()))
        if self.inspector:
            self.inspector.updateContents(reason=reason, initiator=origin)
        else:
            logger.debug("No inspector selected")
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
        if fileNames is None:
            dialog = QtWidgets.QFileDialog(self, caption=caption)

            if rtiRegItem is None:
                nameFilter = 'All files (*);;' # Default show all files.
                nameFilter += self.argosApplication.rtiRegistry.getFileDialogFilter()
            else:
                nameFilter = rtiRegItem.getFileDialogFilter()
                nameFilter += ';;All files (*)'
            dialog.setNameFilter(nameFilter)

            if fileMode:
                dialog.setFileMode(fileMode)

            if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
                fileNames = dialog.selectedFiles()
            else:
                fileNames = []

        fileRootIndex = None
        for fileName in fileNames:
            rtiClass = rtiRegItem.getClass(tryImport=True) if rtiRegItem else None
            fileRootIndex = self.argosApplication.repo.loadFile(fileName, rtiClass=rtiClass)
            self.repoTreeView.setExpanded(fileRootIndex, True)

        # Select last opened file
        if fileRootIndex is not None:
            self.repoTreeView.setCurrentIndex(fileRootIndex)


    def trySelectRtiByPath(self, path):
        """ Selects a repository tree item given a path, expanding nodes if along the way if needed.

            Returns (item, index) if the path was selected successfully, else a warning is logged
            and (None, None) is returned.
        """
        try:
            lastItem, lastIndex = self.repoTreeView.expandPath(path)
            self.repoTreeView.setCurrentIndex(lastIndex)
            return lastItem, lastIndex
        except Exception as ex:
            logger.warn(ex)
            return None, None


    def readViewSettings(self, settings=None): # TODO: rename to readProfile?
        """ Reads the persistent program settings

            :param settings: optional QSettings object which can have a group already opened.
            :returns: True if the header state was restored, otherwise returns False
        """
        if settings is None:
            settings = QtCore.QSettings()
        logger.debug("Reading settings from: {}".format(settings.group()))

        self.restoreGeometry(settings.value("geometry"))
        self.restoreState(settings.value("state"))

        self.repoTreeView.readViewSettings('repo_tree/header_state', settings)
        self.configTreeView.readViewSettings('config_tree/header_state', settings)

        #self._configTreeModel.readModelSettings('config_model', settings)
        settings.beginGroup('cfg_inspectors')
        try:
            for key in settings.childKeys():
                json = settings.value(key)
                self._inspectorsNonDefaults[key] = ctiLoads(json)
        finally:
            settings.endGroup()

        identifier = settings.value("inspector", None)
        try:
            if identifier:
                self.setInspectorById(identifier)
        except KeyError as ex:
            logger.warn("No inspector with ID {!r}.: {}".format(identifier, ex))


    def saveProfile(self, settings=None):
        """ Writes the view settings to the persistent store
        """
        self._updateNonDefaultsForInspector(self.inspectorRegItem, self.inspector)

        if settings is None:
            settings = QtCore.QSettings()
        logger.debug("Writing settings to: {}".format(settings.group()))

        settings.beginGroup('cfg_inspectors')
        try:
            for key, nonDefaults in self._inspectorsNonDefaults.items():
                if nonDefaults:
                    settings.setValue(key, ctiDumps(nonDefaults)) # TODO: do we need JSON?
                    logger.debug("Writing non defaults for {}: {}".format(key, nonDefaults))
        finally:
            settings.endGroup()

        self.configTreeView.saveProfile("config_tree/header_state", settings)
        self.repoTreeView.saveProfile("repo_tree/header_state", settings)

        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("state", self.saveState())

        identifier = self.inspectorRegItem.identifier if self.inspectorRegItem else ''
        settings.setValue("inspector", identifier)


    @QtSlot()
    def cloneWindow(self):
        """ Opens a new window with the same inspector as the current window.
        """
        # Save current window settings.
        settings = QtCore.QSettings()
        settings.beginGroup(self.argosApplication.windowGroupName(self.windowNumber))
        try:
            self.saveProfile(settings)

            # Create new window with the freshly baked settings of the current window.
            name = self.inspectorRegItem.fullName
            newWindow = self.argosApplication.addNewMainWindow(settings=settings,
                                                               inspectorFullName=name)
        finally:
            settings.endGroup()

        # Select the current item in the new window.
        currentItem, _currentIndex = self.repoTreeView.getCurrentItem()
        if currentItem:
            newWindow.trySelectRtiByPath(currentItem.nodePath)

        # Move the new window 24 pixels to the bottom right and raise it to the front.
        newGeomRect = newWindow.geometry()
        logger.debug("newGeomRect: x={}".format(newGeomRect.x()))
        newGeomRect.moveTo(newGeomRect.x() + 24, newGeomRect.y() + 24)

        newWindow.setGeometry(newGeomRect)
        logger.debug("newGeomRect: x={}".format(newGeomRect.x()))

        newWindow.raise_()



    def closeEvent(self, event):
        """ Called when closing this window.
        """
        logger.debug("closeEvent")
        self.argosApplication.saveSettingsIfNeeded()
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


    @QtSlot()
    def addTestData(self):
        """ Adds test data to the repository
        """
        logger.info("Adding test data to the repository.")
        self.argosApplication.repo.insertItem(createArgosTestData())


    @QtSlot()
    def myTest(self):
        """ Function for small ad-hoc tests
        """
        self.testSelectAllData()

        #logger.debug("myTest for window: {}".format(self.windowNumber))
        # logger.debug("Repo icon size: {}".format(self.repoTreeView.iconSize()))
        # #self.repoTreeView.setIconSize(QtCore.QSize(32, 32))
        # self.repoTreeView.setIconSize(QtCore.QSize(24, 24))
        # logger.debug("Repo icon size: {}".format(self.repoTreeView.iconSize()))
        # #self.collector.tree.resizeColumnsToContents(startCol=1)

        # from libargos.qt.misc import printChildren
        # printChildren(self.centralWidget())
        # print()
        # print()
        #
        #
        # self.argosApplication.raiseAllWindows()
        # import gc
        # from libargos.qt import printAllWidgets
        # printAllWidgets(self._argosApplication._qApplication, ofType=MainWindow)
        # print("forcing garbage collection")
        # gc.collect()
        # printAllWidgets(self._argosApplication._qApplication, ofType=MainWindow)

        #for item in self.argosApplication.inspectorRegistry.items:
        #    logger.debug("item: {}".format(item))


    def testSelectAllData(self):
        """ Selects all nodes in a subtree for all inspectors
        """
        # Skip nodes that give known, unfixable errors.
        skipPaths = ['/myDict/numbers/-inf', '/myDict/numbers/nan',
                     '/myDict/numbers/large float'] # in 2D image plot

        def visitNodes(index):
            """ Visits all the nodes recursively.
            """
            assert index.isValid(), "sanity check"

            repoModel = self.repoTreeView.model()
            item = repoModel.getItem(index)
            logger.info("Visiting: {!r} ({} children)".
                        format(item.nodePath, repoModel.rowCount(index)))

            # Select index
            if item.nodePath in skipPaths:
                logger.warn("Skipping node during testing: {}".format(item.nodePath))
                return

            self.repoTreeView.setCurrentIndex(index)
            QtWidgets.qApp.processEvents() # Cause Qt to update UI

            # Expand node to load children.
            #self.repoTreeView.setExpanded(index, True)
            #QtWidgets.qApp.processEvents() # Cause Qt to load children.

            for rowNr in range(repoModel.rowCount(index)):
                childIndex = repoModel.index(rowNr, 0, parentIndex=index)
                visitNodes(childIndex)

        # Actual boddy
        rootNodes = ['/myDict']
        #rootNodes = ['/argos/icm/S5P_ICM_CA_UVN_20120919T051721_20120919T065655_01890_01_001000_20151002T140000.h5']

        for rootNode in rootNodes:
            logger.info("Selecting all nodes in: {}".format(rootNode))

            nodeItem, nodeIndex = self.trySelectRtiByPath(rootNode)
            self.repoTreeView.expandBranch(index = nodeIndex, expanded=True) # TODO: why necessary?
            #QtWidgets.qApp.processEvents()
            visitNodes(nodeIndex)

            #
            # try:
            #
            #     self.repoTreeView.setCurrentIndex(lastIndex)
            # except Exception as ex:
            #     logger.error(ex)
            #     if DEBUGGING:
            #         raise

