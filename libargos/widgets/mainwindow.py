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
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import logging

from .aboutdialog import AboutDialog
from .configtreeview import ConfigTreeView
from .repotreeview import RepoTreeView
from libargos.config.configtreemodel import ConfigTreeModel
from libargos.repo.detailplugins.attr import AttributesPane 
from libargos.inspector.base import BaseInspector
from libargos.info import DEBUGGING, PROJECT_NAME
from libargos.qt import Qt, QtCore, QtGui, QtSlot
from libargos.utils.misc import string_to_identifier


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
        self._instanceNr = MainWindow.__numInstances # Used only for debugging
        MainWindow.__numInstances += 1
        
        self._argosApplication = argosApplication
        self._config = ConfigTreeModel()

        self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
        
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.resize(1300, 700)  # Assumes minimal resolution of 1366 x 768
        self.setWindowTitle("{}-{} (#{})".format(PROJECT_NAME, self.argosApplication.profile, 
                                                 self._instanceNr))
        self.__setupViews()
        self.__setupMenu()
        self.__setupDockWidgets()
        self.__addTestItems()


    @property
    def argosApplication(self):
        """ The ArgosApplication to which this window belongs.
        """
        return self._argosApplication


    def __setupViews(self):
        """ Creates the UI widgets. 
        """
        self.repoTreeView = RepoTreeView(self.argosApplication.repo)
        self.configTreeView = ConfigTreeView(self._config)
        
        temporaryInspector = BaseInspector()
        self.setCentralInspector(temporaryInspector)
        
                              
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
        openFileAction = fileMenu.addAction("&New Inspector Window", 
            self.argosApplication.addNewMainWindow)
        openFileAction.setShortcut(QtGui.QKeySequence.New)

        openDirAction = fileMenu.addAction("Browse Directory...", 
            lambda: self.openFiles(fileMode = QtGui.QFileDialog.Directory))
        openDirAction.setShortcut(QtGui.QKeySequence("Ctrl+B"))
        
        openFileAction = fileMenu.addAction("&Open Files...", 
            lambda: self.openFiles(fileMode = QtGui.QFileDialog.ExistingFiles))
        openFileAction.setShortcut(QtGui.QKeySequence("Ctrl+O"))
        
        openAsMenu = fileMenu.addMenu("Open As")
        for regRti in self.argosApplication.rtiRegistry.registeredRtis:
            rtiClass = regRti.rtiClass
            action = QtGui.QAction(rtiClass.classLabel(), self,
                triggered=lambda: self.openFiles(rtiClass=rtiClass, 
                                                 fileMode = QtGui.QFileDialog.ExistingFiles, 
                                                 caption="Open {}".format(rtiClass.classLabel())))
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
            fileMenu.addAction("&Test-{}".format(self._instanceNr), self.myTest, "Ctrl+T")
                 
        ### View Menu ###
        
        self.viewMenu = menuBar.addMenu("&View")
                
        ### Help Menu ###
                
        menuBar.addSeparator()
        helpMenu = menuBar.addMenu("&Help")
        helpMenu.addAction('&About', self.about)


    def __setupDockWidgets(self):
        """ Sets up the dock widgets. Must be called after the menu is setup.
        """
        # TODO: if the title == "Settings" it won't be added to the view menu.
        self.dockWidget(self.repoTreeView, "Repository", Qt.LeftDockWidgetArea) 
        self.dockWidget(self.configTreeView, "Application Settings", Qt.RightDockWidgetArea) 

        self.attributesPane = AttributesPane(self.repoTreeView)
        self.dockDetailPane(self.attributesPane, area=Qt.LeftDockWidgetArea)


    # -- End of setup_methods --
    
    def dockWidget(self, widget, title, area):
        """ Adds a widget as a docked widget.
            Returns the added dockWidget
        """
        assert widget.parent() is None, "Inspector already has a parent"
        
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
        dockWidget.visibilityChanged.connect(detailPane.dockVisibilityChanged) 
        return dockWidget

    
    def setCentralInspector(self, inspector):
        """ Sets the central inspector widget
        """
        self.setCentralWidget(inspector)
        
        

    # TODO: to repotreemodel? Note that the functionality will be common to selectors.
    @QtSlot() 
    def openFiles(self, fileNames=None, rtiClass=None, caption=None, fileMode=None):
        """ Lets the user select on or more files and opens it.

            :param fileNames: If None an open-file dialog allows the user to select files,
                otherwise the files are opened directly.
            :param rtiClass: Open the files as this type of repository tree item. None=autodetect.
            :param caption: Optional caption for the file dialog.
            :param fileMode: is passed to the file dialog.
            :rtype fileMode: QtGui.QFileDialog.FileMode constant 
        """
        if fileNames is None:
            dialog = QtGui.QFileDialog(self, caption=caption)
            if fileMode:
                dialog.setFileMode(fileMode)
                
            if dialog.exec_() == QtGui.QFileDialog.Accepted:
                fileNames = dialog.selectedFiles()
            else:
                fileNames = []
            
        for fileName in fileNames:
            storeRootIndex = self.argosApplication.repo.loadFile(fileName, rtiClass=rtiClass)
            self.repoTreeView.setExpanded(storeRootIndex, True)
    
    
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
        self._config.readModelSettings('config_model', settings)
        

    def saveProfile(self, settings=None):
        """ Writes the view settings to the persistent store
        """         
        if settings is None:
            settings = QtCore.QSettings()  
        logger.debug("Writing settings to: {}".format(settings.group()))
        
        self._config.saveProfile('config_model', settings)
        self.configTreeView.saveProfile("config_tree/header_state", settings)
        self.repoTreeView.saveProfile("repo_tree/header_state", settings)
                    
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("state", self.saveState())

 
    def closeEvent(self, event):
        """ Called when closing this window.
        """
        logger.debug("closeEvent")
        self.argosApplication.saveProfileIfNeeded()
        self.argosApplication.removeMainWindow(self)
        event.accept()
        logger.debug("closeEvent accepted")
        
        
    def about(self):
        """ Shows the about message window. 
        """
        aboutDialog = AboutDialog(parent=self)
        aboutDialog.show()
        aboutDialog.addDependencyInfo()

        
    def myTest(self):
        """ Function for testing """
        logger.debug("myTest for window: {}".format(self._instanceNr))
        
        try:
            self.__show_error += 1
        except:
            self.__show_error = 0
            
        if self.__show_error % 2 == 0:            
            self.attributesPane.drawError(msg="Debug Error")
        else:
            self.attributesPane.drawContents()
        
#        self.argosApplication.raiseAllWindows()
#        import gc
#        from libargos.qt import printAllWidgets
#        printAllWidgets(self._argosApplication._qApplication, ofType=MainWindow)
#        print("forcing garbage collection")
#        gc.collect()
#        printAllWidgets(self._argosApplication._qApplication, ofType=MainWindow)



    def __addTestItems(self):
        """ Temporary function to add test CTIs
        """
        from libargos.config.basecti import BaseCti
        from libargos.config.simplectis import IntegerCti, StringCti, BoolCti, ChoiceCti, ColorCti
        
        rootItem = BaseCti(nodeName='line color', defaultValue=123)
        rootIndex = self._config.insertItem(rootItem)
        self.configTreeView.setExpanded(rootIndex, True) # does not work because of read settings

        rootItem.insertChild(IntegerCti(nodeName='line-1 color', defaultValue=-7, minValue = -5, stepSize=2))
        
        self._config.insertItem(StringCti(nodeName='letter', defaultValue='aa', maxLength = 1))
        self._config.insertItem(BoolCti(nodeName='grid', defaultValue=True))

        self._config.insertItem(ChoiceCti(nodeName='hobbit', defaultValue=2, 
                                          choices=['Frodo', 'Sam', 'Pippin', 'Merry']))

        self._config.insertItem(ColorCti(nodeName='favorite color', defaultValue="#22FF33"))
    
