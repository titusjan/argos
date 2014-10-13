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
# along with Argos.  If not, see <http://www.gnu.org/licenses/>.

""" 
    Main window functionality
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import logging, platform

from .info import DEBUGGING, PROJECT_NAME, VERSION, PROJECT_URL
from .qt import executeApplication, Qt, QtCore, QtGui, USE_PYQT
from .qt.togglecolumn import ToggleColumnTreeView


logger = logging.getLogger(__name__)



def createBrowser(fileName = None, **kwargs):
    """ Opens an MainWindow window
    """
    # Assumes qt.getQApplicationInstance() has been executed.
    browser = MainWindow(**kwargs)
    if fileName is not None:
        browser.openFile(fileName)
    browser.show()
    if platform.system() == 'Darwin':
        browser.raise_()
    return browser
        

def browse(fileName = None, **kwargs):
    """ Opens and executes a main window
    """
    _object_browser = createBrowser(fileName = fileName, **kwargs)
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
        
        # Model
        pass
    
        # Views
        self.__setupActions()
        self.__setupMenu()
        self.__setupViews()
        self.setWindowTitle("{}".format(PROJECT_NAME))
        app = QtGui.QApplication.instance()
        app.lastWindowClosed.connect(app.quit) 

        self._readViewSettings(reset = reset)
            
        logger.debug("MainWindow constructor finished")
     

    def __setupActions(self):
        """ Creates the main window actions.
        """
        pass
                  
                              
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
        if DEBUGGING is True:
            fileMenu.addSeparator()
            fileMenu.addAction("&Test", self.myTest, "Ctrl+T")
        
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
        
        self.treeView = ToggleColumnTreeView(self)
        centralLayout.addWidget(self.treeView)        
        
        self.label2 = QtGui.QLabel("Hi there", parent=self)
        centralLayout.addWidget(self.label2)        
        
        # Connect signals
        pass

    # End of setup_methods
    
    def loadFile(self, fileName):
        """ Loads a pstats file and updates the table model
        """
        logger.debug("Loading file: {}".format(fileName))
        #TODO: implement
        

    def openFile(self, fileName=None): 
        """ Lets the user select a pstats file and opens it.
        """
        if not fileName:
            fileName = QtGui.QFileDialog.getOpenFileName(self, 
                caption = "Choose a pstats file", directory = '', 
                filter='All files (*);;MyExtension (*.ext;*.ex)')
            if not USE_PYQT:
                # PySide returns: (file, selectedFilter)
                fileName = fileName[0]

        if fileName:
            logger.info("Loading data from: {!r}".format(fileName))
            try:
                self.loadFile(fileName)
            except Exception as ex:
                if DEBUGGING:
                    raise
                else:
                    logger.error("Error opening file: %s", ex)
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
            

    def myTest(self):
        """ Function for testing """
        logger.debug("myTest")
        logger.debug("row height: {}".format(self.tableView.rowHeight(0)))
        
    def about(self):
        """ Shows the about message window. """
        message = u"{} version {}\n\n{}""".format(PROJECT_NAME, VERSION, PROJECT_URL)
        QtGui.QMessageBox.about(self, "About {}".format(PROJECT_NAME), message)

    def closeWindow(self):
        """ Closes the window """
        self.close()
        
    def quitApplication(self):
        """ Closes all windows """
        app = QtGui.QApplication.instance()
        app.closeAllWindows()

    def closeEvent(self, event):
        """ Close all windows (e.g. the L0 window).
        """
        logger.debug("closeEvent")
        self._writeViewSettings()
        self.close()
        event.accept()
            
