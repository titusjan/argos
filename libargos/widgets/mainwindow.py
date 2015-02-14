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

from .repotreeview import RepoTreeView
from libargos.repo.registry import getRtiRegistry
from libargos.repo.repotreemodel import getGlobalRepository
from libargos.info import DEBUGGING, PROJECT_NAME, VERSION, PROJECT_URL
from libargos.qt import QtCore, QtGui, QtSlot

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

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self._argosApplication = argosApplication
        
        self.__setupViews()
        self.__setupMenu()
        
        # Connect signals
        #self.fileMenu.aboutToShow.connect(self.treeView.updateCurrentItemActions) # TODO: needed?
        self.destroyed.connect(self.byebye) # TODO: remove
        
        self.setWindowTitle("{}-{}".format(PROJECT_NAME, self.argosApplication.profile))
        self.resize(QtCore.QSize(1024, 700))
        
        if DEBUGGING:
            self.__addTestData()

    
    @property
    def argosApplication(self):
        """ The ArgosApplication to which this window belongs.
        """
        return self._argosApplication


    def __setupViews(self):
        """ Creates the UI widgets. 
        """
        #self.mainWidget = QtGui.QWidget(self)
        #self.setCentralWidget(self.mainWidget)
        
        self.mainSplitter = QtGui.QSplitter(self, orientation = QtCore.Qt.Vertical)
        self.setCentralWidget(self.mainSplitter)
        centralLayout = QtGui.QVBoxLayout()
        self.mainSplitter.setLayout(centralLayout)
        
        self.treeView = RepoTreeView(getGlobalRepository())
        centralLayout.addWidget(self.treeView)
        
        self.label2 = QtGui.QLabel("Hi there", parent=self)
        centralLayout.addWidget(self.label2)    
        
                              
    def __setupMenu(self):
        """ Sets up the main menu.
        """
        if 1: # TODO: 0/1???
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
        
        openFileAction = fileMenu.addAction("&Open Files...", 
            lambda: self.openFiles(fileMode = QtGui.QFileDialog.ExistingFiles))
        openFileAction.setShortcut(QtGui.QKeySequence("Ctrl+O, F"))

        openDirAction = fileMenu.addAction("Open Directory...", 
            lambda: self.openFiles(fileMode = QtGui.QFileDialog.Directory))
        openDirAction.setShortcut(QtGui.QKeySequence("Ctrl+O, D"))
        
        openAsMenu = fileMenu.addMenu("Open As")
        for regRti in getRtiRegistry().registeredRtis:
            rtiClass = regRti.rtiClass
            action = QtGui.QAction(rtiClass.getLabel(), self,
                triggered=lambda: self.openFiles(rtiClass=rtiClass, 
                                                 fileMode = QtGui.QFileDialog.ExistingFiles, 
                                                 caption="Open {}".format(rtiClass.getLabel())))
            openAsMenu.addAction(action)

        for action in self.treeView.topLevelItemActionGroup.actions():
            fileMenu.addAction(action)
            
        for action in self.treeView.currentItemActionGroup.actions():
            fileMenu.addAction(action)

        fileMenu.addSeparator()
        fileMenu.addAction("Close &Window", self.close, QtGui.QKeySequence.Close)
        fileMenu.addAction("E&xit", self.argosApplication.closeAllWindows, QtGui.QKeySequence.Quit)
        if DEBUGGING:
            fileMenu.addSeparator()
            fileMenu.addAction("&Test-{}".format(self._instanceNr), self.myTest, "Ctrl+T")
                 
        ### Help Menu ###
                
        menuBar.addSeparator()
        helpMenu = menuBar.addMenu("&Help")
        helpMenu.addAction('&About', self.about)

    # -- End of setup_methods --

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
            
        repo = getGlobalRepository()
        for fileName in fileNames:
            storeRootIndex = repo.loadFile(fileName, rtiClass=rtiClass)
            self.treeView.setExpanded(storeRootIndex, True)
    
    
    def readViewSettings(self, settings=None):
        """ Reads the persistent program settings
            
            :param settings: optional QSettings object which can have a group already opened.
            :returns: True if the header state was restored, otherwise returns False
        """ 
        if settings is None:
            settings = QtCore.QSettings()  
        logger.debug("Reading settings from: {}".format(settings.group()))
        
        windowSize = settings.value("window_size", None)
        if windowSize:
            self.resize(windowSize)
            
        windowPos = settings.value("window_pos", None)
        if windowPos:
            self.move(windowPos) 
                                 
        splitterState = settings.value("main_splitter/state")
        if splitterState:
            self.mainSplitter.restoreState(splitterState)
        self.treeView.readViewSettings('repo_tree/header_state', settings)
        

    def writeViewSettings(self, settings=None):
        """ Writes the view settings to the persistent store
        """         
        if settings is None:
            settings = QtCore.QSettings()  
        logger.debug("Writing settings to: {}".format(settings.group()))
        
        self.treeView.writeViewSettings("repo_tree/header_state", settings)
        settings.setValue("main_splitter/state", self.mainSplitter.saveState())        
        settings.setValue("window_pos", self.pos())
        settings.setValue("window_size", self.size())
            

    def __addTestData(self):
        """ Temporary function to add test data
        """
        import numpy as np
        from libargos.repo.memoryrti import MappingRti
        myDict = {}
        myDict['name'] = 'Pac Man'
        myDict['age'] = 34
        myDict['ghosts'] = ['Inky', 'Blinky', 'Pinky', 'Clyde']
        myDict['array'] = np.arange(24).reshape(3, 8)
        myDict['subDict'] = {'mean': np.ones(111), 'stddev': np.zeros(111, dtype=np.uint16)}
        
        mappingRti = MappingRti(myDict, nodeName="myDict", fileName='')
        storeRootIndex = getGlobalRepository().insertItem(mappingRti)
        self.treeView.setExpanded(storeRootIndex, False)
        self.treeView.setCurrentIndex(storeRootIndex)



    def myTest(self):
        """ Function for testing """
        logger.debug("myTest for window: {}".format(self._instanceNr))
        
        self.argosApplication.raiseAllWindows()
        
        import gc
        
        from libargos.qt import printChildren, printAllWidgets
        printAllWidgets(self._argosApplication._qApplication, ofType=MainWindow)

        logger.debug("forcing garbage collection")
        gc.collect()
        printAllWidgets(self._argosApplication._qApplication, ofType=MainWindow)
        
      
        
    def about(self): # TODO: to application
        """ Shows the about message window. """
        message = "{} version {}\n\n{}".format(PROJECT_NAME, VERSION, PROJECT_URL)
        QtGui.QMessageBox.about(self, "About {}".format(PROJECT_NAME), message)


    #def close(self):
    #    """ Closes the window """
    #   logger.debug("Called closeWindow")
    #    self.close()
    #    return True
        
 
    def closeEvent(self, event):
        """ Called when closing this window.
        """
        logger.debug("closeEvent")
        self.argosApplication.writeViewSettingsIfNeeded()
        self.argosApplication.removeMainWindow(self)
        event.accept()
        logger.debug("closeEvent accepted")
            
            
    @QtSlot()            
    def destroy(self, *args, **kwargs): # TODO: remove
        """ Frees up window system resources. Overridden to be able to log this. 
            This function is usually called from the QWidget destructor.
        """
        logger.debug("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&\n\n")
        logger.debug("{}.destroy({}, {}): {}".format(self, *args, **kwargs))
        super(MainWindow, self).destroy(*args, **kwargs)

    @QtSlot()            
    def byebye(self, obj): # TODO: remove
        """ Called when qobject is destroyed
        """
        logger.debug("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&\n\n")
        logger.debug("{}.byebye: {}".format(self, obj))
