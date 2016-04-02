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
from libargos.collect.collector import Collector
from libargos.config.abstractcti import ctiDumps, ctiLoads
from libargos.config.abstractcti import AbstractCti
from libargos.config.configtreemodel import ConfigTreeModel
from libargos.config.configtreeview import ConfigTreeView
from libargos.info import DEBUGGING, PROJECT_NAME
from libargos.inspector.dialog import OpenInspectorDialog
from libargos.inspector.registry import InspectorRegItem
from libargos.qt import Qt, QtCore, QtGui, QtSlot

from libargos.repo.detailplugins.attr import AttributesPane
from libargos.repo.detailplugins.dim import DimensionsPane
from libargos.repo.detailplugins.prop import PropertiesPane
from libargos.repo.repotreeview import RepoTreeView
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


class MainWindow(QtGui.QMainWindow):
    """ Main application window.
    """
    __numInstances = 0
    
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
        self._persistentSettings = {}  # non-default values for all used plugins

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
        self.__setupMenu()
        self.__setupDockWidgets()

        
    def finalize(self):
        """ Is called before destruction (when closing). 
            Can be used to clean-up resources.
        """
        logger.debug("Finalizing: {}".format(self))
        
        # Disconnect signals
        self.collector.contentsChanged.disconnect(self.collectorContentsChanged)
        self._configTreeModel.itemChanged.disconnect(self.configContentsChanged)


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
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.setContentsMargins(CENTRAL_MARGIN, CENTRAL_MARGIN, CENTRAL_MARGIN, CENTRAL_MARGIN)
        layout.setSpacing(CENTRAL_SPACING)
        self.setCentralWidget(widget)
        
        # Must be after setInspector since that already draws the inspector
        self.collector.contentsChanged.connect(self.collectorContentsChanged)
        self._configTreeModel.itemChanged.connect(self.configContentsChanged)
        
                              
    def __setupMenu(self):
        """ Sets up the main menu.
        """
        if True: 
            # Don't use self.menuBar(), on OS-X this is not shared across windows.
            # See: http://qt-project.org/doc/qt-4.8/qmenubar.html#details
            # And:http://qt-project.org/doc/qt-4.8/qmainwindow.html#menuBar
            menuBar = QtGui.QMenuBar() # Make a menu without parent.
            self.setMenuBar(menuBar)
        else:
            menuBar = self.menuBar()  

        ### File Menu ###

        fileMenu = menuBar.addMenu("&File")

        action = fileMenu.addAction("&Set Inspector...", self.openInspector)
        action.setShortcut(QtGui.QKeySequence("Ctrl+i")) 
        
        action = fileMenu.addAction("&New Window...", self.argosApplication.addNewMainWindow)
        action.setShortcut(QtGui.QKeySequence("Ctrl+N")) # TODO. Should open inspector selection window
        
        action = fileMenu.addAction("&Clone Window", self.argosApplication.addNewMainWindow)
        action.setShortcut(QtGui.QKeySequence("Ctrl+Shift+N"))
        
        fileMenu.addSeparator()

        action = fileMenu.addAction("Browse Directory...", 
            lambda: self.openFiles(fileMode = QtGui.QFileDialog.Directory))
        action.setShortcut(QtGui.QKeySequence("Ctrl+B"))
        
        action = fileMenu.addAction("&Open Files...", 
            lambda: self.openFiles(fileMode = QtGui.QFileDialog.ExistingFiles))
        action.setShortcut(QtGui.QKeySequence("Ctrl+O"))
        
        openAsMenu = fileMenu.addMenu("Open As")
        for rtiRegItem in self.argosApplication.rtiRegistry.items:
            #rtiRegItem.tryImportClass()
            def createTrigger():
                "Function to create a closure with the regItem"
                _rtiRegItem = rtiRegItem # keep reference in closure
                return lambda: self.openFiles(rtiRegItem=_rtiRegItem, 
                                              fileMode = QtGui.QFileDialog.ExistingFiles, 
                                              caption="Open {}".format(_rtiRegItem.name))

            action = QtGui.QAction("{}...".format(rtiRegItem.name), self,
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
        if DEBUGGING:
            fileMenu.addSeparator()
            fileMenu.addAction("&Test-{}".format(self.windowNumber), self.myTest, "Ctrl+T")
                 
        ### View Menu ###
        
        self.viewMenu = menuBar.addMenu("&View")

        action = self.viewMenu.addAction("Installed &Plugins...", self.openPluginsDialog)  
        action.setShortcut(QtGui.QKeySequence("Ctrl+P"))
        
        self.viewMenu.addSeparator()
        ### Help Menu ###
                
        menuBar.addSeparator()
        helpMenu = menuBar.addMenu("&Help")
        helpMenu.addAction('&About', self.about)


    def __setupDockWidgets(self):
        """ Sets up the dock widgets. Must be called after the menu is setup.
        """
        # TODO: if the title == "Settings" it won't be added to the view menu.
        self.dockWidget(self.repoTreeView, "Data Repository", Qt.LeftDockWidgetArea) 
        self.dockWidget(self.collector, "Data Collector", Qt.TopDockWidgetArea) 
        self.dockWidget(self.configTreeView, "Application Settings", Qt.RightDockWidgetArea) 

        self.viewMenu.addSeparator()
        
        propertiesPane = PropertiesPane(self.repoTreeView)
        self.dockDetailPane(propertiesPane, area=Qt.LeftDockWidgetArea)

        attributesPane = AttributesPane(self.repoTreeView)
        self.dockDetailPane(attributesPane, area=Qt.LeftDockWidgetArea)

        dimensionsPane = DimensionsPane(self.repoTreeView)
        self.dockDetailPane(dimensionsPane, area=Qt.LeftDockWidgetArea)


    # -- End of setup_methods --
    
    def dockWidget(self, widget, title, area):
        """ Adds a widget as a docked widget.
            Returns the added dockWidget
        """
        assert widget.parent() is None, "Widget already has a parent"
        
        dockWidget = QtGui.QDockWidget(title, parent=self)
        dockWidget.setObjectName("dock_" + string_to_identifier(title))
        dockWidget.setWidget(widget)
        
        self.addDockWidget(area, dockWidget)
        self.viewMenu.addAction(dockWidget.toggleViewAction())
        return dockWidget
    
    
    def dockDetailPane(self, detailPane, title=None, area=None):
        """ Calls addDockedWidget to add a repo detail pane with a default title.
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


    def setInspectorById(self, identifier):
        """ Sets the central inspector widget given a inspector ID.
            Will raise a KeyError if the ID is not found in the registry.
            
            NOTE: does not draw the new inspector, this is the responsibility of the caller.
        """
        inspectorRegistry = self.argosApplication.inspectorRegistry
        inspectorRegItem = inspectorRegistry.getItemById(identifier)
        self.setInspectorFromRegItem(inspectorRegItem)
        
        
    def setInspectorFromRegItem(self, inspectorRegItem):
        """ Sets the central inspector widget given a inspectorRegItem.

            Does NOT draw the new inspector, this is the responsibility of the caller.
            It does however update the inspector node in the config tree.

            If inspectorRegItem is None, the inspector will be unset. Also, if the underlying class 
            cannot be imported a warning is logged and the inspector is unset.
              
        """
        check_class(inspectorRegItem, InspectorRegItem, allow_none=True)
        
        logger.debug("setInspectorFromRegItem: {}. Disabling updates.".format(inspectorRegItem))
        self.setUpdatesEnabled(False)
        try:
            centralLayout = self.centralWidget().layout()
            
            # Delete old inspector
            if self.inspector is None: # can be None at start-up
                oldConfigPosition = None
            else:
                # Remove old inspector configuration from tree            
                oldConfigPosition = self.inspector.config.childNumber()
                configPath = self.inspector.config.nodePath
                _, oldConfigIndex = self._configTreeModel.findItemAndIndexPath(configPath)[-1]
                self._configTreeModel.deleteItemAtIndex(oldConfigIndex)
                            
                self.inspector.finalize()
                centralLayout.removeWidget(self.inspector)
                self.inspector.deleteLater()
                
            # Set new inspector
            self._inspectorRegItem = inspectorRegItem
            if inspectorRegItem is None:
                self._inspector = None
            else:
                try:
                    self._inspector = inspectorRegItem.create(self.collector, tryImport=True)
                except ImportError as ex:
                    logger.warn("Clearing inspector. Unable to create {!r} because {}"
                                .format(inspectorRegItem.identifier, ex))
                    self._inspector = None

            self.setWindowTitle(self.constructWindowTitle())
            
            # Update collector widgets and the config tree
            oldBlockState = self.collector.blockSignals(True)
            try:
                if self.inspector is None:
                    self.collector.clearAndSetComboBoxes([])
                else:
                    key = self.inspectorRegItem.identifier
                    nonDefaults = self._persistentSettings.get(key, {})
                    self.inspector.config.setValuesFromDict(nonDefaults)
                    self._configTreeModel.insertItem(self.inspector.config, oldConfigPosition)
                    self.configTreeView.expandBranch()  
                    self.collector.clearAndSetComboBoxes(self.inspector.axesNames())
                    centralLayout.addWidget(self.inspector)
            finally:
                self.collector.blockSignals(oldBlockState)
        finally:
            logger.debug("setInspectorFromRegItem: {}. Enabling updates.".format(inspectorRegItem))
            self.setUpdatesEnabled(True)


    @QtSlot()
    def openInspector(self):
        """ Opens the inspector dialog box to let the user change the current inspector.
        """
        dialog = OpenInspectorDialog(self.argosApplication.inspectorRegistry, parent=self)
        dialog.setCurrentInspectorRegItem(self.inspectorRegItem)
        dialog.exec_()
        if dialog.result():
            inspectorRegItem = dialog.getCurrentInspectorRegItem()
            if inspectorRegItem is not None: 
                self.setInspectorFromRegItem(inspectorRegItem)
                self.drawInspectorContents()
        
    @QtSlot()
    def openPluginsDialog(self):
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
        self.drawInspectorContents()

        
    @QtSlot(AbstractCti)
    def configContentsChanged(self, configTreeItem):
        """ Slot is called when an item has been changed by setData of the ConfigTreeModel. 
            Will draw the window contents.
        """
        logger.debug("configContentsChanged: {}".format(configTreeItem))
        self.drawInspectorContents()

        # Store the old config values for persistence. Must be done after the inspector was drawn
        # because this may update some derived config values (e.g. ranges)
        if self.inspectorRegItem and self.inspector:
            key = self.inspectorRegItem.identifier
            self._persistentSettings[key] = self.inspector.config.getNonDefaultsDict()

            
    def drawInspectorContents(self):
        """ Draws all contents of this window's inspector.
        """
        logger.debug("")
        logger.debug("-------- Drawing inspector of window: {} --------".format(self.windowTitle()))
        if self.inspector:
            try:
                logger.debug("x-autorange: {!r}".format(self.inspector.configValue('axes/x-axis/range/auto-range')))
                logger.debug("y-autorange: {!r}".format(self.inspector.configValue('axes/y-axis/range/auto-range')))
            except:
                pass
            self.inspector.drawContents()
        else:
            logger.debug("No inspector selected")
    

    # TODO: to repotreemodel? Note that the functionality will be common to selectors.
    @QtSlot() 
    def openFiles(self, fileNames=None, rtiRegItem=None, caption=None, fileMode=None):
        """ Lets the user select on or more files and opens it.

            :param fileNames: If None an open-file dialog allows the user to select files,
                otherwise the files are opened directly.
            :param rtiRegItem: Open the files as this type of registered RTI. None=autodetect.
            :param caption: Optional caption for the file dialog.
            :param fileMode: is passed to the file dialog.
            :rtype fileMode: QtGui.QFileDialog.FileMode constant 
        """
        if fileNames is None:
            dialog = QtGui.QFileDialog(self, caption=caption)
            
            if rtiRegItem is None:
                nameFilter = 'All files (*);;' # Default show all files.
                nameFilter += self.argosApplication.rtiRegistry.getFileDialogFilter()
            else:
                nameFilter = rtiRegItem.getFileDialogFilter()
                nameFilter += ';;All files (*)'
            dialog.setNameFilter(nameFilter)
            
            if fileMode:
                dialog.setFileMode(fileMode)
                
            if dialog.exec_() == QtGui.QFileDialog.Accepted:
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
        """ Selects a repository tree item given a path.

            Returns True if the path was selected succesfully, else a warning is logged and False
            is returned.
        """
        try:
            _lastItem, lastIndex = self.repoTreeView.expandPath(path)
            self.repoTreeView.setCurrentIndex(lastIndex)
            return True
        except Exception as ex:
            logger.warn(ex)
            return False


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
                self._persistentSettings[key] = ctiLoads(json) 
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
        if settings is None:
            settings = QtCore.QSettings()  
        logger.debug("Writing settings to: {}".format(settings.group()))
        
        settings.beginGroup('cfg_inspectors')
        try:
            for key, nonDefaults in self._persistentSettings.items():
                if nonDefaults:
                    settings.setValue(key, ctiDumps(nonDefaults)) # TODO: do we need JSON?
        finally:
            settings.endGroup()
        
        self.configTreeView.saveProfile("config_tree/header_state", settings)
        self.repoTreeView.saveProfile("repo_tree/header_state", settings)
                    
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("state", self.saveState())
        
        identifier = self.inspectorRegItem.identifier if self.inspectorRegItem else ''
        settings.setValue("inspector", identifier)

 
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
    def myTest(self):
        """ Function for testing """
        logger.debug("myTest for window: {}".format(self.windowNumber))

        self.collector.tree.resizeColumnsToContents(startCol=1)

#        from libargos.qt.misc import printChildren
#        printChildren(self.centralWidget())
#        print()
#        print()
        
        
#        self.argosApplication.raiseAllWindows()
#        import gc
#        from libargos.qt import printAllWidgets
#        printAllWidgets(self._argosApplication._qApplication, ofType=MainWindow)
#        print("forcing garbage collection")
#        gc.collect()
#        printAllWidgets(self._argosApplication._qApplication, ofType=MainWindow)




