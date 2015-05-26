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

from libargos.inspector.base import BaseInspector
from libargos.qt import QtGui

logger = logging.getLogger(__name__)


class DebugInspector(BaseInspector):
    """ Inspector for debugging purposes.
        Shows the shape of the selected array
    """
    _label = "Debug Inspector"
    
    
    def __init__(self, collector, parent=None):
        
        super(DebugInspector, self).__init__(collector, parent=parent)
        
        self.label = QtGui.QLabel()
        self.contentsLayout.addWidget(self.label)
        

    def _drawContents(self):
        """ Draws the inspector widget when no input is available.
            The default implementation shows an error message. Descendants should override this.
        """
        text = str(self.collector.rti)
        logger.debug("@@@@@@@@ _drawContents: {}".format(text))
        self.label.setText(text)

