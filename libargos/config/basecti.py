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

""" Repository TreeItem (RTI) classes
    Tree items for use in the RepositoryTreeModel
"""
import logging, os

from libargos.info import program_directory, DEBUGGING
from libargos.qt import QtGui # TODO: get rid of dependency on QtGui?
from libargos.qt.treeitems import BaseTreeItem
from libargos.utils.cls import StringType, check_class, is_a_sequence

ICONS_DIRECTORY = os.path.join(program_directory(), 'img/icons')

logger = logging.getLogger(__name__)


class BaseCti(BaseTreeItem):
    """ TreeItem for use in a ConfigTreeModel. (RTI = Config TreeItem)
        Base node from which to derive the other types of nodes.

        Serves as an interface but can also be instantiated for debugging purposes.
    """
    _label = "Unknown Item"
    
    def __init__(self, nodeName='', value=None, defaultValue=None):
        """ Constructor
        
            :param nodeName: name of this node (used to construct the node path).
            :param fileName: absolute path to the file where the data of this RTI originates.
        """
        super(BaseCti, self).__init__(nodeName=nodeName)

        self._type = int
        self._value = self.type(value)
        self._defaultValue = defaultValue
         
    
    @classmethod
    def classLabel(cls):
        """ Returns a short string that describes this class. For use in menus, headers, etc. 
        """
        return cls._label
    
    @property
    def value(self):
        """ Returns the value of this item. 
        """
        return self._value

    @value.setter
    def value(self, value):
        """ Sets the value of this item. 
        """
        self._value = self.type(value)
            
    @property
    def defaultValue(self):
        """ Returns the default value of this item. 
        """
        return self._defaultValue
            
    @property
    def type(self):
        """ Returns type of the value of this item. 
        """
        return self._type
