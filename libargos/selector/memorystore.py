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
import logging

logger = logging.getLogger(__name__)

from libargos.selector.abstractstore import BaseRti, LazyLoadRti

from libargos.utils import (check_is_a_sequence, check_is_a_mapping, check_is_an_array,  
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
    

class SequenceRti(LazyLoadRti):
    
    def __init__(self, sequence, nodeName=None):
        """ Constructor
        """
        super(SequenceRti, self).__init__(nodeName=nodeName)
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
        
    def fetchChildren(self):
        assert self.canFetchChildren(), "canFetchChildren must be True"
        childItems = []
        for nr, elem in enumerate(self._sequence):
            childItems.append(_createFromObject(elem, nodeName="elem-{}".format(nr)))

        self._childrenFetched = True
        return childItems
    


class MappingRti(LazyLoadRti):
    
    def __init__(self, dictionary, nodeName=None):
        """ Constructor
        """
        super(MappingRti, self).__init__(nodeName=nodeName)
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
        
    def fetchChildren(self):
        assert self.canFetchChildren(), "canFetchChildren must be True"
        childItems = []
        for key, value in sorted(self._dictionary.items()):
            childItems.append(_createFromObject(value, nodeName=str(key)))
            
        self._childrenFetched = True
        return childItems

