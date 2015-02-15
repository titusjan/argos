""" 
    'About' dialog window that shows version information.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import logging

from libargos.utils import moduleinfo as mi
from libargos.info import PROJECT_NAME, VERSION
from libargos.qt import QtCore, QtGui


logger = logging.getLogger(__name__)


# The main window inherits from a Qt class, therefore it has many 
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201 


class AboutDialog(QtGui.QDialog): 
    """ Dialog window that shows dependency information.
    """
    def __init__(self, *args, **kwargs):
        """ Constructor
        """
        super(AboutDialog, self).__init__(*args, **kwargs)
        self.setModal(True)
        
        mainLayout = QtGui.QVBoxLayout()
        self.setLayout(mainLayout)
        
        progVersionLabel = QtGui.QLabel()
        progVersionLabel.setText("{} {}".format(PROJECT_NAME, VERSION))
        progVersionLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        mainLayout.addWidget(progVersionLabel)
        
        self.editor = QtGui.QTextEdit()
        self.editor.setReadOnly(True)
        
        font = QtGui.QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(13)

        self.editor = QtGui.QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setFont(font)
        self.editor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.editor.clear()
        self.editor.setPlainText("Retrieving package info...")        
        mainLayout.addWidget(self.editor)
        
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)
        mainLayout.addWidget(buttonBox)
        
        self.resize(QtCore.QSize(800, 400))
        
        
    def addDependencyInfo(self):
        """ Adds version info about the installed dependencies
        """
        logger.debug("Adding dependency info to the AboutDialog")
                
        self.editor.clear()
        self.editor.setPlainText("Retrieving package info...")
        
        miList = []
        miList.append(mi.PythonModuleInfo())
        miList.append(mi.PyQt4ModuleInfo())
        
        modules = ['PySide', 'numpy', 'scipy', 'pyqtgraph', 'matplotlib', 'yaml']
        for module in modules:
            miList.append(mi.ImportedModuleInfo(module))

        miList.append(mi.H5pyModuleInfo())
        miList.append(mi.NetCDF4ModuleInfo())   

        self.editor.clear()
        lines = []
        for info in miList:
            lines.append ("{:12s}: {}".format(info.name, info.verboseVersion))     
        
        self.editor.setPlainText('\n'.join(lines))

        logger.debug("Finished adding dependency info to the AboutDialog")
                

