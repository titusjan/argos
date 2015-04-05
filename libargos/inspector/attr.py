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

""" Variable attributes inspector. 
"""
import logging

from .base import BaseInspector
from libargos.qt import Qt, QtGui
from libargos.qt.togglecolumn import ToggleColumnTableWidget

logger = logging.getLogger(__name__)

class AttributeInspector(BaseInspector):
    """ Shows the attributes of the selected variable
    """
    _label = "Attribute Inspector"
    
    def __init__(self, parent=None):
        super(AttributeInspector, self).__init__(parent)
        
        self.table = ToggleColumnTableWidget(5, 2)
        self.contentsLayout.addWidget(self.table)
        
    
        


        
        
        