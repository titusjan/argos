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

from .basetable import BaseTableInspector
from libargos.widgets.constants import COL_ELEM_TYPE_WIDTH

logger = logging.getLogger(__name__)



class AttributeInspector(BaseTableInspector):
    """ Shows the attributes of the selected variable
    """
    _label = "Attribute Inspector"
    
    HEADERS = ["Name", "Value", "Type"]
    (COL_ATTR_NAME, COL_VALUE, COL_ELEM_TYPE) = range(len(HEADERS))
    
    def __init__(self, parent=None):
        super(AttributeInspector, self).__init__(AttributeInspector.HEADERS, parent=parent)
        self.table.addHeaderContextMenu(enabled = {'Name': False, 'Value': False}, 
                                        checked = {'Type': False}) 
    
        tableHeader = self.table.horizontalHeader()
        tableHeader.resizeSection(self.COL_ATTR_NAME, 125)
        tableHeader.resizeSection(self.COL_VALUE, 150)  
        tableHeader.resizeSection(self.COL_ELEM_TYPE, COL_ELEM_TYPE_WIDTH)          

        
        