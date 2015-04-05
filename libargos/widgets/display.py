""" Widgets for displaying messages
"""
from __future__ import print_function

import logging

from libargos.qt import Qt, QtGui


logger = logging.getLogger(__name__)


# The main window inherits from a Qt class, therefore it has many 
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201 


class MessageDisplay(QtGui.QWidget):
    """ Widget that shows a label and title.
        Consists of a title label and a larger message label for details.
    """
    def __init__(self, parent=None, msg="", title="Error"):
        super(MessageDisplay, self).__init__(parent)    
        
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


