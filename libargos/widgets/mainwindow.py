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

import logging, platform

from .repotree import RepoTree
from libargos.state.commonstate import getCommonState
from libargos.info import DEBUGGING, PROJECT_NAME, VERSION, PROJECT_URL
from libargos.qt import executeApplication, QtCore, QtGui, USE_PYQT, QtSlot

logger = logging.getLogger(__name__)



def createBrowser(fileNames = tuple(), **kwargs):
    """ Opens an MainWindow window
    """
    # Assumes qt.getQApplicationInstance() has been executed.
    browser = MainWindow(**kwargs)
    for fileName in fileNames:
        browser.openFile(fileName)
    browser.show()
    if platform.system() == 'Darwin':
        browser.raise_()
    return browser
        

def browse(fileNames = None, **kwargs):
    """ Opens and executes a main window
    """
    _object_browser = createBrowser(fileNames = fileNames, **kwargs)
    exit_code = executeApplication()
    return exit_code

        
# The main window inherits from a Qt class, therefore it has many 
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201 


class MainWindow(QtGui.QMainWindow):
    """ Main application window.
    """
    _nInstances = 0
    
    def __init__(self, reset = False):
        """ Constructor
            :param reset: If true the persistent settings, such as column widths, are reset. 
        """
        super(MainWindow, self).__init__()

        MainWindow._nInstances += 1
        self._InstanceNr = self._nInstances        
        
        self.__setupActions()
        self.__setupMenu()
        self.__setupViews()
        
        self.setWindowTitle("{}".format(PROJECT_NAME))
        app = QtGui.QApplication.instance()
        app.lastWindowClosed.connect(app.quit) 

        self._readViewSettings(reset = reset)

        # Update model 
        self.__addTestData()


    def __setupActions(self):
        """ Creates the main window actions.
        """
        self.insertChildAction = QtGui.QAction("Insert Child", self)
        self.insertChildAction.setShortcut("Ctrl+N")

        self.deleteItemAction = QtGui.QAction("Delete Item", self)
        self.deleteItemAction.setShortcut("Ctrl+D")
        
        self.openFileAction = QtGui.QAction("Open File", self)
        self.openFileAction.setShortcut("Ctrl+O")
        
        self.closeFileAction = QtGui.QAction("Close File", self)
        self.closeFileAction.setShortcut("Ctrl+P") # TODO: remove shortcut
                  
                              
    def __setupMenu(self):
        """ Sets up the main menu.
        """
        # Don't use self.menuBar(), on OS-X this is not shared across windows.
        menuBar = QtGui.QMenuBar() # Make a menu without parent.
        self.setMenuBar(menuBar)

        fileMenu = menuBar.addMenu("&File")
        openAction = fileMenu.addAction("&Open...", self.openFile)
        openAction.setShortcut("Ctrl+O")
        fileMenu.addAction("C&lose", self.closeWindow, "Ctrl+W")
        fileMenu.addAction("E&xit", self.quitApplication, "Ctrl+Q")
        if True or DEBUGGING is True: # TODO: remove True clause
            fileMenu.addSeparator()
            fileMenu.addAction("&Test", self.myTest, "Ctrl+T")
        
        actionsMenu = menuBar.addMenu("&Actions")
        actionsMenu.addAction(self.insertChildAction)
        actionsMenu.addAction(self.deleteItemAction)

        actionsMenu.addAction(self.openFileAction)
        actionsMenu.addAction(self.closeFileAction)
                
        menuBar.addSeparator()
        help_menu = menuBar.addMenu("&Help")
        help_menu.addAction('&About', self.about)
        

    def __setupViews(self):
        """ Creates the UI widgets. 
        """
        #self.mainWidget = QtGui.QWidget(self)
        #self.setCentralWidget(self.mainWidget)
        
        self.mainSplitter = QtGui.QSplitter(self, orientation = QtCore.Qt.Vertical)
        self.setCentralWidget(self.mainSplitter)
        centralLayout = QtGui.QVBoxLayout()
        self.mainSplitter.setLayout(centralLayout)
        
        self.treeView = RepoTree(getCommonState().repository.treeModel)
        centralLayout.addWidget(self.treeView)
        
        self.label2 = QtGui.QLabel("Hi there", parent=self)
        centralLayout.addWidget(self.label2)        
        
        # Connect signals and slots 
        self.insertChildAction.triggered.connect(self.treeView.insertItem)
        self.deleteItemAction.triggered.connect(self.treeView.removeRow)
        self.openFileAction.triggered.connect(self.treeView.openSelectedFile)
        self.closeFileAction.triggered.connect(self.treeView.closeSelectedFile)


    # -- End of setup_methods --

    def openFile(self, fileName=None): 
        """ Lets the user select an Ascii file and opens it.
        """
        if not fileName:
            fileName = QtGui.QFileDialog.getOpenFileName(self, 
                caption = "Choose a file", directory = '', 
                filter='Txt (*.txt;*.text);;netCDF(*.nc;*.nc4);;All files (*)')
            if not USE_PYQT:
                # PySide returns: (file, selectedFilter)
                fileName = fileName[0]

        if fileName:
            logger.info("Loading data from: {!r}".format(fileName))
            try:
                self.treeView.loadFile(fileName, expand = True)
            except Exception as ex:
                if DEBUGGING:
                    raise
                else:
                    # TODO: message box with retry / close old file.
                    logger.error("Error opening file: {}".format(ex))
                    QtGui.QMessageBox.warning(self, "Error opening file", str(ex))
    
    
    def _settingsGroupName(self, prefix):
        """ Creates a setting group name based on the prefix and instance number
        """
        settingsGroup = "window{:02d}-{}".format(self._InstanceNr, prefix)
        logger.debug("  settings group is: {!r}".format(settingsGroup))
        return settingsGroup    
        
    
    def _readViewSettings(self, reset=False):
        """ Reads the persistent program settings
        
            :param reset: If True, the program resets to its default settings
        """ 
        pos = QtCore.QPoint(20 * self._InstanceNr, 20 * self._InstanceNr)
        windowSize = QtCore.QSize(1024, 700)
        
        if reset:
            logger.debug("Resetting persistent view settings")
        else:
            logger.debug("Reading view settings for window: {:d}".format(self._InstanceNr))
            settings = QtCore.QSettings()
            settings.beginGroup(self._settingsGroupName('view'))
            pos = settings.value("main_window/pos", pos)
            windowSize = settings.value("main_window/size", windowSize)
            splitterState = settings.value("main_splitter/state")
            if splitterState:
                self.mainSplitter.restoreState(splitterState)
            settings.endGroup()
            
        logger.debug("windowSize: {!r}".format(windowSize))
        self.resize(windowSize)
        self.move(pos)


    def _writeViewSettings(self):
        """ Writes the view settings to the persistent store
        """         
        logger.debug("Writing view settings for window: {:d}".format(self._InstanceNr))
        
        settings = QtCore.QSettings()
        settings.beginGroup(self._settingsGroupName('view'))
        settings.setValue("main_splitter/state", self.mainSplitter.saveState())        
        settings.setValue("main_window/pos", self.pos())
        settings.setValue("main_window/size", self.size())
        settings.endGroup()
            

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
        
        mappingRti = MappingRti(myDict, nodeName="myDict")
        storeRootIndex = getCommonState().repository.appendTreeItem(mappingRti)
        self.treeView.setExpanded(storeRootIndex, True)

        selectionModel = self.treeView.selectionModel()
        selectionModel.setCurrentIndex(storeRootIndex, QtGui.QItemSelectionModel.ClearAndSelect)
        logger.debug("selected tree item: has selection: {}".format(selectionModel.hasSelection()))
        

    def myTest(self):
        """ Function for testing """
        logger.debug("myTest")
        selectionModel = self.treeView.selectionModel()
        logger.debug("selected tree item: has selection: {}".format(selectionModel.hasSelection()))
        raise AssertionError("False positive")
        
    def about(self):
        """ Shows the about message window. """
        message = "{} version {}\n\n{}".format(PROJECT_NAME, VERSION, PROJECT_URL)
        QtGui.QMessageBox.about(self, "About {}".format(PROJECT_NAME), message)

    def closeWindow(self):
        """ Closes the window """
        self.close()
        
    def quitApplication(self):
        """ Closes all windows """
        app = QtGui.QApplication.instance()
        app.closeAllWindows()

    def closeEvent(self, event):
        """ Called when closing all windows.
        """
        logger.debug("closeEvent")
        self._writeViewSettings()
        self.close()
        event.accept()
            
