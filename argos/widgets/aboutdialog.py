"""
    'About' dialog window that shows version information.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import logging

from argos.info import PROJECT_NAME, VERSION
from argos.qt import QtCore, QtGui, QtWidgets
from argos.utils.cls import is_a_string
from argos.utils import moduleinfo as mi
from argos.widgets.constants import MONO_FONT, FONT_SIZE

logger = logging.getLogger(__name__)


# The main window inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201


class AboutDialog(QtWidgets.QDialog):
    """ Dialog window that shows dependency information.
    """
    def __init__(self, parent=None):
        """ Constructor
        """
        super(AboutDialog, self).__init__(parent=parent)
        self.setModal(True)

        mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(mainLayout)

        progVersionLabel = QtWidgets.QLabel()
        progVersionLabel.setText("{} {}".format(PROJECT_NAME, VERSION))
        progVersionLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        mainLayout.addWidget(progVersionLabel)

        font = QtGui.QFont()
        font.setFamily(MONO_FONT)
        font.setFixedPitch(True)
        font.setPointSize(FONT_SIZE)

        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setFont(font)
        self.editor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.editor.clear()
        self.editor.setPlainText("Retrieving package info...")
        mainLayout.addWidget(self.editor)

        self.progressLabel = QtWidgets.QLabel()
        mainLayout.addWidget(self.progressLabel)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)
        mainLayout.addWidget(buttonBox)

        self.resize(QtCore.QSize(800, 400))


    def _addModuleInfo(self, moduleInfo):
        """ Adds a line with module info to the editor
            :param moduleInfo: can either be a string or a module info class.
                In the first case, an object is instantiated as ImportedModuleInfo(moduleInfo).
        """
        if is_a_string(moduleInfo):
            moduleInfo = mi.ImportedModuleInfo(moduleInfo)

        line = "{:15s}: {}".format(moduleInfo.name, moduleInfo.verboseVersion)
        self.editor.appendPlainText(line)
        QtWidgets.QApplication.instance().processEvents()


    def addDependencyInfo(self):
        """ Adds version info about the installed dependencies
        """
        logger.debug("Adding dependency info to the AboutDialog")
        self.progressLabel.setText("Retrieving package info...")
        self.editor.clear()

        self._addModuleInfo(mi.PythonModuleInfo())
        self._addModuleInfo(mi.QtModuleInfo())

        modules = ['numpy', 'scipy', 'pandas', 'pyqtgraph']
        for module in modules:
            self._addModuleInfo(module)

        self._addModuleInfo(mi.PillowInfo())
        self._addModuleInfo(mi.H5pyModuleInfo())
        self._addModuleInfo(mi.NetCDF4ModuleInfo())

        self.progressLabel.setText("")
        logger.debug("Finished adding dependency info to the AboutDialog")

