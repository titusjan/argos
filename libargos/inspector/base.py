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

""" Base class for inspectors
"""
import logging, os

from libargos.info import program_directory, DEBUGGING
from libargos.qt import Qt, QtGui

logger = logging.getLogger(__name__)

TEMP_ERROR = """Traceback (most recent call last):
  File "/Users/titusjan/Programming/python/argos/argos", line 27, in <module>
    from libargos import browse
  File "/Users/titusjan/Programming/python/argos/libargos/__init__.py", line 26, in <module>
    from .application import ArgosApplication
  File "/Users/titusjan/Programming/python/argos/libargos/application.py", line 28, in <module>
    from libargos.widgets.mainwindow import MainWindow
  File "/Users/titusjan/Programming/python/argos/libargos/widgets/mainwindow.py", line 31, in <module>
    from libargos.inspector.base import BaseInspector
  File "/Users/titusjan/Programming/python/argos/libargos/inspector/base.py", line 68
    centralLayout.addWidget(self.errorLabel)
"""

# TODO: is-a-widget or has-a-widget?

class BaseInspector(QtGui.QWidget):
    """ Base class for inspectors.
        Serves as an interface but can also be instantiated for debugging purposes.
    """
    _label = "Unknown Inspector"
    
    def __init__(self, parent=None):
        super(BaseInspector, self).__init__(parent)
        
        self._selector = None
        self._collector = None
        
        self.__setupViews()
        

    @classmethod
    def classLabel(cls):
        """ Returns a short string that describes this class. For use in menus, headers, etc. 
        """
        return cls._label
            
    
    def __setupViews(self):
        """ Creates the UI widgets. 
        """
        #self.mainWidget = QtGui.QWidget(self)
        #self.setCentralWidget(self.mainWidget)
        
        centralLayout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
        self.setLayout(centralLayout)
        
        self.errorTitleLabel = QtGui.QLabel("Error")
        self.errorTitleLabel.setTextFormat(Qt.PlainText)
        self.errorTitleLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.errorTitleLabel.setAlignment(Qt.AlignHCenter)
        centralLayout.addWidget(self.errorTitleLabel, stretch=0)
        
        font = QtGui.QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(13)
        
        self.errorMessageLabel = QtGui.QLabel(TEMP_ERROR)
        self.errorMessageLabel.setFont(font)
        self.errorMessageLabel.setTextFormat(Qt.PlainText)
        self.errorMessageLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.errorMessageLabel.setWordWrap(True)
        self.errorMessageLabel.setAlignment(Qt.AlignTop)
        self.errorMessageLabel.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Plain)
        centralLayout.addWidget(self.errorMessageLabel, stretch=1)

        