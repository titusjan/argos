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


from .repotreeview import RepoTreeView
from libargos.repo.registry import getRtiRegistry
from libargos.repo.repotreemodel import getGlobalRepository
from libargos.info import DEBUGGING, PROJECT_NAME, VERSION, PROJECT_URL
from libargos.qt import executeApplication, QtCore, QtGui, QtSlot
#from libargos.widgets.gcmonitor import createGcMonitor

logger = logging.getLogger(__name__)


def createBrowser(fileNames = tuple(), **kwargs):
    """ Opens an MainWindow window
    """
    # Assumes qt.getQApplicationInstance() has been executed.
    browser = MainWindow(**kwargs)
    browser.openFiles(fileNames=fileNames)
    browser.show()
    if platform.system() == 'Darwin':
        browser.raise_()
    return browser
        

def browse(fileNames = None, **kwargs):
    """ Opens and executes a main window
    """
    _browser = createBrowser(fileNames = fileNames, **kwargs)
    #if DEBUGGING: # TODO temporary
    #    _gcMon = createGcMonitor()
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

        self._instanceNr = self._nInstances        
        MainWindow._nInstances += 1
        
        self.__setupViews()
        self.__setupMenu()
        
        # Connect signals
        #self.fileMenu.aboutToShow.connect(self.treeView.updateCurrentItemActions) # TODO: needed?
        
        self.setWindowTitle("{}".format(PROJECT_NAME))
        app = QtGui.QApplication.instance()
        app.lastWindowClosed.connect(app.quit) 

        self._readViewSettings(reset = reset)

        # Update model 
        self.__addTestData()


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
        # Don't use self.menuBar(), on OS-X this is not shared across windows.
        menuBar = QtGui.QMenuBar() # Make a menu without parent.
        self.setMenuBar(menuBar)

        ### File Menu ###

        fileMenu = menuBar.addMenu("&File")
        openFileAction = fileMenu.addAction("&Open Files...", 
            lambda: self.openFiles(fileMode = QtGui.QFileDialog.ExistingFiles))
        openFileAction.setShortcut("Ctrl+O, F")

        openDirAction = fileMenu.addAction("Open Directory...", 
            lambda: self.openFiles(fileMode = QtGui.QFileDialog.Directory))
        openDirAction.setShortcut("Ctrl+O, D")
        
        openAsMenu = fileMenu.addMenu("Open As")
        for regRti in getRtiRegistry().registeredRtis:
            rtiClass = regRti.rtiClass
            action = QtGui.QAction(rtiClass.getLabel(), self,
                triggered=lambda: self.openFiles(rtiClass=rtiClass, 
                                                 fileMode = QtGui.QFileDialog.ExistingFiles, 
                                                 caption="Open {}".format(rtiClass.getLabel())))
            openAsMenu.addAction(action)

        for action in self.treeView.currentItemActionGroup.actions():
            fileMenu.addAction(action)

        for action in self.treeView.topLevelItemActionGroup.actions():
            fileMenu.addAction(action)

        fileMenu.addSeparator()
        fileMenu.addAction("Close &Window", self.closeWindow, "Ctrl+W")
        fileMenu.addAction("E&xit", self.quitApplication, "Ctrl+Q")
        if DEBUGGING:
            fileMenu.addSeparator()
            fileMenu.addAction("&Test", self.myTest, "Ctrl+T")
                 
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
            
        for fileName in fileNames:
            logger.info("Loading data from: {!r}".format(fileName))
            try:
                self.treeView.loadFile(fileName, expand = True, rtiClass=rtiClass)
            except Exception as ex: # TODO: still needed?
                if DEBUGGING:
                    raise
                else:
                    logger.error("Error opening file: {}".format(ex))
                    QtGui.QMessageBox.warning(self, "Error opening file", str(ex))
    
    
    def _settingsGroupName(self, prefix=''):
        """ Creates a setting group name based on the prefix and instance number
        """
        settingsGroup = "window-{:02d}{}".format(self._instanceNr, prefix)
        return settingsGroup    
        
    
    def _readViewSettings(self, reset=False):
        """ Reads the persistent program settings
        
            :param reset: If True, the program resets to its default settings
        """ 
        settings = QtCore.QSettings()
        if reset:
            logger.debug("Resetting persistent settings for window: {:d}".format(self._instanceNr))
            settings.remove(self._settingsGroupName())
            
        logger.debug("Reading settings for window: {:d}".format(self._instanceNr))
        settings.beginGroup(self._settingsGroupName())
        
        self.resize(settings.value("window_size", QtCore.QSize(1024, 700)))
        self.move(settings.value("window_pos", 
                                 QtCore.QPoint(20 * self._instanceNr, 20 * self._instanceNr)))
        
        splitterState = settings.value("main_splitter/state")
        if splitterState:
            self.mainSplitter.restoreState(splitterState)
        self.treeView.readViewSettings('repo_tree/header_state', settings)
        settings.endGroup()
        

    def _writeViewSettings(self):
        """ Writes the view settings to the persistent store
        """         
        #logger.debug("Writing settings: {}".format(settings.fileName()))
        logger.debug("Writing persistent settings for window: {:d}".format(self._instanceNr))
        
        settings = QtCore.QSettings()
        settings.beginGroup(self._settingsGroupName())
        self.treeView.writeViewSettings("repo_tree/header_state", settings)
        settings.setValue("main_splitter/state", self.mainSplitter.saveState())        
        settings.setValue("window_pos", self.pos())
        settings.setValue("window_size", self.size())
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
        
        mappingRti = MappingRti(myDict, nodeName="myDict", fileName='')
        storeRootIndex = getGlobalRepository().insertItem(mappingRti)
        self.treeView.setExpanded(storeRootIndex, False)
        self.treeView.setCurrentIndex(storeRootIndex)
        

    def myTest(self):
        """ Function for testing """
        logger.debug("myTest")
        
        self._logViewSettings()
        
#        selectionModel = self.treeView.selectionModel()
#        hasCurrent = selectionModel.currentIndex().isValid()
#        logger.debug("hasCurrent: {}, hasSelection: {}"
#                     .format(hasCurrent, selectionModel.hasSelection()))
#        selectionModel.clearSelection()
#        
        #import numpy as np
        #from netCDF4 import Dataset 
        #arr = np.loadtxt('/Users/titusjan/Data/argos/fel_nist/pruts3.txt')
        #logger.debug("Array shape: {}".format(arr.shape))
        #del arr
        
        #ds = Dataset('/Users/titusjan/Data/argos/fel_nist/test.nc', 'r', format='NETCDF4')
        #logger.debug("ds: {}".format(ds))
        
        
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
            
