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

""" Store and Tree items for representing data that is stored in memory.
"""
import logging, os

logger = logging.getLogger(__name__)

from .treeitems import ICONS_DIRECTORY, BaseRti, LazyLoadRtiMixin

from libargos.qt import QtGui
from libargos.utils.cls import (check_is_a_sequence, check_is_a_mapping, check_is_an_array,  
                                is_a_sequence, is_a_mapping, is_an_array, type_name)


def _createFromObject(obj, nodeName):
    if is_a_sequence(obj):
        return SequenceRti(obj, nodeName=nodeName)
    elif is_a_mapping(obj):
        return MappingRti(obj, nodeName=nodeName)
    elif is_an_array(obj):
        return ArrayRti(obj, nodeName=nodeName)
    else:
        return ScalarRti(obj, nodeName=nodeName)
    

class ScalarRti(BaseRti):
    """ Stores a Python or numpy scalar
    """
    _icon = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'asterisk.svg'))
    
    def __init__(self, scalar, nodeName=None):
        super(ScalarRti, self).__init__(nodeName = nodeName)
        self._scalar = scalar 
    
    @property
    def typeName(self):
        return type_name(self._scalar)
    
    @property
    def elementTypeName(self):
        return self.typeName
    

class ArrayRti(BaseRti):

    _icon = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'th-large.svg'))
    
    def __init__(self, array, nodeName=None):
        """ Constructor
        """
        super(ArrayRti, self).__init__(nodeName=nodeName)
        check_is_an_array(array)
        self._array = array
   
    @property
    def arrayShape(self):
        return self._array.shape

    @property
    def typeName(self):
        return type_name(self._array)
    
    @property
    def elementTypeName(self):
        dtype =  self._array.dtype
        return '<compound>' if dtype.names else str(dtype)
    

class SequenceRti(LazyLoadRtiMixin, BaseRti):
    
    _icon = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'th-large.svg'))
    
    def __init__(self, sequence, nodeName=None):
        """ Constructor
        """
        LazyLoadRtiMixin.__init__(self)
        BaseRti.__init__(self, nodeName=nodeName)
        check_is_a_sequence(sequence)
        self._sequence = sequence
   
    @property
    def arrayShape(self):
        return (len(self._sequence), )

    @property
    def typeName(self):
        return type_name(self._sequence)
    
    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children 
        """
        return len(self._sequence) > 0
        
    def _fetchAllChildren(self):
        """ Adds a child item for each column 
        """
        childItems = []
        for nr, elem in enumerate(self._sequence):
            childItems.append(_createFromObject(elem, nodeName="elem-{}".format(nr)))

        return childItems
    


class MappingRti(LazyLoadRtiMixin, BaseRti):
    
    _icon = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'folder-open.svg'))
    
    def __init__(self, dictionary, nodeName=None):
        """ Constructor
        """
        LazyLoadRtiMixin.__init__(self)
        BaseRti.__init__(self, nodeName=nodeName)
        check_is_a_mapping(dictionary)
        self._dictionary = dictionary

    @property
    def arrayShape(self):
        return (len(self._dictionary), )

    @property
    def typeName(self):
        return type_name(self._dictionary)
    
    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children 
        """
        return len(self._dictionary) > 0
        
    def _fetchAllChildren(self):
        """ Adds a child item for each item 
        """        
        childItems = []
        for key, value in sorted(self._dictionary.items()):
            childItems.append(_createFromObject(value, nodeName=str(key)))
            
        return childItems

