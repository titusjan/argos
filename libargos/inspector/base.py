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
from libargos.info import DEBUGGING
from libargos.qt import QtGui, QtSlot
from libargos.utils.cls import type_name
from libargos.widgets.constants import DOCK_SPACING, DOCK_MARGIN, LEFT_DOCK_WIDTH
from libargos.widgets.display import MessageDisplay

logger = logging.getLogger(__name__)


class BaseInspector(QtGui.QStackedWidget):
    """ Base class for inspectors.
        Serves as an interface but can also be instantiated for debugging purposes.
        An inspector is a stacked widget; it has a contents page and and error page.
    """
    _label = "Base Inspector"
    
    ERROR_PAGE_IDX = 0
    CONTENTS_PAGE_IDX = 1
    
    def __init__(self, collector, parent=None):
        
        super(BaseInspector, self).__init__(parent)
        
        self._collector = collector
        
        self.errorWidget = MessageDisplay()
        self.addWidget(self.errorWidget)

        self.contentsWidget = QtGui.QWidget()
        self.addWidget(self.contentsWidget)

        self.contentsLayout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
        self.contentsLayout.setSpacing(DOCK_SPACING)
        self.contentsLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)        
        self.contentsWidget.setLayout(self.contentsLayout)
        
        self.setCurrentIndex(self.CONTENTS_PAGE_IDX)

    @classmethod
    def classLabel(cls):
        """ Returns a short string that describes this class. For use in menus, headers, etc. 
        """
        return cls._label
    
    @property
    def collector(self):
        """ The data collector from where this inspector gets its data
        """
        return self._collector
     
#        
#    def sizeHint(self):
#        """ The recommended size for the widget."""
#        return QtCore.QSize(LEFT_DOCK_WIDTH, 250)
        
    
    @QtSlot()
    def draw(self):
        """ Tries to draw the widget contents. 
            Shows the error page in case an exceptionis raised while drawing the contents.
        """
        try:
            self.setCurrentIndex(self.CONTENTS_PAGE_IDX)
            self._drawContents()
        except Exception as ex:
            self.setCurrentIndex(self.ERROR_PAGE_IDX)
            self._drawError(msg=str(ex), title=type_name(ex))
            if DEBUGGING:
                raise
            
    
    def _drawContents(self):
        """ Draws the inspector widget contents.
            The default implementation shows an empty page (no widgets). Descendants should 
            override this.
        """
        pass
        

    def _drawError(self, msg="", title="Error"):
        """ Shows and error message.
        """
        self.errorWidget.setError(msg=msg, title=title)
        
        
        