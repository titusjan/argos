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

from libargos.info import DEBUGGING, PROJECT_NAME, VERSION, PROJECT_URL
from libargos.qt import executeApplication, Qt, QtCore, QtGui, USE_PYQT, QtSlot
from libargos.qt.togglecolumn import ToggleColumnTreeView
from libargos.selector.repository import Repository
from libargos.selector.datastore import SimpleTextFileStore


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
        
        self._repository = Repository()
    
        self.__setupActions()
        self.__setupMenu()
        self.__setupViews()
        
        self.setWindowTitle("{}".format(PROJECT_NAME))
        app = QtGui.QApplication.instance()
        app.lastWindowClosed.connect(app.quit) 

        self._readViewSettings(reset = reset)

        # Update model 
        #self.__addTestData()

     

    def __setupActions(self):
        """ Creates the main window actions.
        """
        self.insertChildAction = QtGui.QAction("Insert Child", self)
        self.insertChildAction.setShortcut("Ctrl+N")           

        self.deleteItemAction = QtGui.QAction("Delete Item", self)
        self.deleteItemAction.setShortcut("Ctrl+D")           
                  
                              
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
        self.treeView.setModel(self._repository.treeModel) # TODO: use a selector with its own model
        self.treeView.setAlternatingRowColors(True)
        self.treeView.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems) # TODO: SelectRows
        self.treeView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.treeView.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.treeView.setAnimated(True)
        self.treeView.setAllColumnsShowFocus(True)        
        centralLayout.addWidget(self.treeView)
        
        treeHeader = self.treeView.header()
        treeHeader.setMovable(True)
        treeHeader.setStretchLastSection(False)  
        treeHeader.resizeSection(0, 200)
        headerNames = self.treeView.model().horizontalHeaders
        enabled = dict((name, True) for name in headerNames)
        enabled[headerNames[0]] = False # Fist column cannot be unchecked
        self.treeView.addHeaderContextMenu(enabled=enabled)
        
        self.label2 = QtGui.QLabel("Hi there", parent=self)
        centralLayout.addWidget(self.label2)        
        
        # Connect signals and slots 
        self.insertChildAction.triggered.connect(self.insertItem)
        self.deleteItemAction.triggered.connect(self.removeRow)


    # End of setup_methods
    
    def loadTextFile(self, fileName):
        """ Loads a pstats file and updates the table model
        """
        logger.debug("Loading file: {}".format(fileName))
        textFileStore = SimpleTextFileStore(fileName)
        textFileStore.open()
        storeRootIndex = self._repository.appendStore(textFileStore)
        self.treeView.setExpanded(storeRootIndex, True)
        

    def openFile(self, fileName=None): 
        """ Lets the user select an Ascii file and opens it.
        """
        if not fileName:
            fileName = QtGui.QFileDialog.getOpenFileName(self, 
                caption = "Choose a pstats file", directory = '', 
                filter='Txt (*.txt;*.text);;All files (*)')
            if not USE_PYQT:
                # PySide returns: (file, selectedFilter)
                fileName = fileName[0]

        if fileName:
            logger.info("Loading data from: {!r}".format(fileName))
            try:
                self.loadTextFile(fileName)
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
            

    def __addTestData(self):
        """ Temporary function to add test data
        """
        #assert False, "not yet operational"
        self._model.addScalar("six", 6)
        self._model.addScalar("seven", 7)
        self._model.addScalar("eight", 8)
        self._model.addScalar("nine", 9)
        childIndex = self._model.addScalar("ten", 10)
        
        selectionModel = self.treeView.selectionModel()
        selectionModel.setCurrentIndex(childIndex, QtGui.QItemSelectionModel.ClearAndSelect)
        logger.debug("selected tree item: has selection: {}".format(selectionModel.hasSelection()))
        
        
    @QtSlot()
    def insertItem(self):
        """ Temporary test method
        """
        import random
        selectionModel = self.treeView.selectionModel()
        assert selectionModel.hasSelection(), "No selection"        
        curIndex = selectionModel.currentIndex()
        col0Index = curIndex.sibling(curIndex.row(), 0)
        
        model = self.treeView.model()
        value = random.randint(20, 99)
        childIndex = model.addScalar("new child", value, position=None, parentIndex=col0Index)
        
        self.treeView.selectionModel().setCurrentIndex(childIndex, 
                                                       QtGui.QItemSelectionModel.ClearAndSelect)
        
        newChildItem = model.getItem(childIndex, altItem=model.rootItem)
        logger.debug("Added child: {} under {}".format(newChildItem, newChildItem.parentItem))

        #self.updateActions() # TODO: needed?        
        
        
    @QtSlot()    
    def removeRow(self):
        """ Temporary test method
        """
        logger.debug("RemoveRow()")
        selectionModel = self.treeView.selectionModel()
        assert selectionModel.hasSelection(), "No selection"
        self.treeView.model().deleteItem(selectionModel.currentIndex())
        logger.debug("removeRow completed")        
            

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
            
