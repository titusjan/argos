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
import logging
from libargos.qt import Qt, QtGui

logger = logging.getLogger(__name__)


class InspectorErrorWidget(QtGui.QWidget):
    """ The page of an inspector that is shown in case of an error.
        Consists of a title label and a larger message label for details.
    """
    def __init__(self, parent=None, msg="", title="Error"):
        super(InspectorErrorWidget, self).__init__(parent)    
        
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        
        self.titleLabel = QtGui.QLabel(title)
        self.titleLabel.setTextFormat(Qt.PlainText)
        self.titleLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.titleLabel.setAlignment(Qt.AlignHCenter)
        self.layout.addWidget(self.titleLabel, stretch=0)
        
        font = QtGui.QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(13)
        
        self.messageLabel = QtGui.QLabel(msg)
        self.messageLabel.setFont(font)
        self.messageLabel.setTextFormat(Qt.PlainText)
        self.messageLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.messageLabel.setWordWrap(True)
        self.messageLabel.setAlignment(Qt.AlignTop)
        self.messageLabel.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Plain)
        self.layout.addWidget(self.messageLabel, stretch=1)    
    
    
    def setError(self, msg=None, title=None):
        """ Shows and error message
        """
        if msg is not None:
            self.messageLabel.setText(msg)
            
        if title is not None:    
            self.titleLabel.setText(title)


class BaseInspector(QtGui.QStackedWidget):
    """ Base class for inspectors.
        Serves as an interface but can also be instantiated for debugging purposes.
        An inspector is a stacked widget; it has a contents page and and error page.
    """
    _label = "Unknown Inspector"
    
    ERROR_PAGE_IDX = 0
    CONTENTS_PAGE_IDX = 1
    
    def __init__(self, parent=None):
        super(BaseInspector, self).__init__(parent)
        
        #self._selector = None
        #self._collector = None
        
        self.errorWidget = InspectorErrorWidget()
        self.addWidget(self.errorWidget)

        self.contentsWidget = QtGui.QWidget() # will be overridden in descendants
        self.addWidget(self.contentsWidget)

        self.contentsLayout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
        self.contentsWidget.setLayout(self.contentsLayout)
        
        self.setCurrentIndex(self.CONTENTS_PAGE_IDX)

    @classmethod
    def classLabel(cls):
        """ Returns a short string that describes this class. For use in menus, headers, etc. 
        """
        return cls._label
        

    def drawEmpty(self):
        """ Draws the inspector widget when no input is available.
            The default implementation shows an error message. Descendants should override this.
        """
        self.setCurrentIndex(self.CONTENTS_PAGE_IDX)
        

    def drawError(self, msg="", title="Error"):
        """ Shows and error message
        """
        self.errorWidget.setError(msg=msg, title=title)
        self.setCurrentIndex(self.ERROR_PAGE_IDX)
        
        
        