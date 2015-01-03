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

from .treeitems import ICONS_DIRECTORY, BaseRti

from libargos.qt import QtGui
from libargos.utils.cls import (check_is_a_sequence, check_is_a_mapping, check_is_an_array,  
                                is_a_sequence, is_a_mapping, is_an_array, type_name)


_ICOLOR = 'FF0000' 


def _createFromObject(obj, nodeName, fileName):
    if is_a_sequence(obj):
        return SequenceRti(obj, nodeName=nodeName, fileName=fileName)
    elif is_a_mapping(obj):
        return MappingRti(obj, nodeName=nodeName, fileName=fileName)
    elif is_an_array(obj):
        return ArrayRti(obj, nodeName=nodeName, fileName=fileName)
    else:
        return ScalarRti(obj, nodeName=nodeName, fileName=fileName)
    

class ScalarRti(BaseRti):
    """ Stores a Python or numpy scalar
    """
    _iconOpen = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'asterisk.{}.svg'.format(_ICOLOR)))
    _iconClosed = _iconOpen      
    
    def __init__(self, scalar, nodeName='', fileName=''):
        super(ScalarRti, self).__init__(nodeName = nodeName, fileName=fileName)
        self._scalar = scalar 
    
    @property
    def typeName(self):
        return type_name(self._scalar)
    
    @property
    def elementTypeName(self):
        return self.typeName
    
    def hasChildren(self):
        """ Returns False. Leaf nodes never have children. """
        return False
    

class ArrayRti(BaseRti):
    """ Represents a numpy array (or None for undefined)
    """
    _iconOpen = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'th-large.{}.svg'.format(_ICOLOR)))
    _iconClosed = _iconOpen     

    def __init__(self, array, nodeName='', fileName=''):
        """ Constructor. 
            :param array: the underlying array. May be undefined (None)
            :type array: numpy.ndarray or None
        """
        super(ArrayRti, self).__init__(nodeName=nodeName, fileName=fileName)
        check_is_an_array(array, allow_none=True) # TODO: what about masked arrays?
        self._array = array
   
    @property
    def arrayShape(self):
        if self._array is None:
            return super(ArrayRti, self).arrayShape 
        else:
            return self._array.shape

    @property
    def typeName(self):
        return type_name(self._array)
    
    @property
    def elementTypeName(self):
        if self._array is None:
            return super(ArrayRti, self).elementTypeName 
        else:        
            dtype =  self._array.dtype
            return '<compound>' if dtype.names else str(dtype)

    def hasChildren(self):
        """ Returns False. Leaf nodes never have children. """
        return False
    
    

class SequenceRti(BaseRti):
    """ Represents a sequence (e.g. a list or a tuple)
    """
    
    _iconOpen = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'th-large.{}.svg'.format(_ICOLOR)))
    _iconClosed = _iconOpen     
    
    def __init__(self, sequence, nodeName='', fileName=''):
        """ Constructor. 
            :param sequence: the underlying sequence. May be undefined (None)
            :type array: None or a Python sequence (e.g. list or tuple)
        """
        BaseRti.__init__(self, nodeName=nodeName, fileName=fileName)
        check_is_a_sequence(sequence, allow_none=True)
        self._sequence = sequence
   
    @property
    def arrayShape(self):
        if self._sequence is None:
            return super(SequenceRti, self).arrayShape 
        else:
            return (len(self._sequence), )

    @property
    def typeName(self):
        return type_name(self._sequence)
    
        
    def _fetchAllChildren(self):
        """ Adds a child item for each column 
        """
        childItems = []
        for nr, elem in enumerate(self._sequence):
            childItems.append(_createFromObject(elem, nodeName="elem-{}".format(nr), 
                                                fileName=self.fileName))
        return childItems
    


class MappingRti(BaseRti):
    
    _iconOpen = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'folder-open.{}.svg'.format(_ICOLOR)))
    _iconClosed = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'folder-close.{}.svg'.format(_ICOLOR)))
    
    def __init__(self, dictionary, nodeName='', fileName=''):
        """ Constructor
        """
        BaseRti.__init__(self, nodeName=nodeName, fileName=fileName)
        check_is_a_mapping(dictionary)
        self._dictionary = dictionary

    @property
    def arrayShape(self):
        return (len(self._dictionary), )

    @property
    def typeName(self):
        return type_name(self._dictionary)
        
    def _fetchAllChildren(self):
        """ Adds a child item for each item 
        """        
        childItems = []
        logger.debug("{!r} _fetchAllChildren {!r}".format(self, self.fileName))
        for key, value in sorted(self._dictionary.items()):
            childItems.append(_createFromObject(value, nodeName=str(key), fileName=self.fileName))
            
        return childItems

