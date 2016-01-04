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
import numpy as np

from .baserti import ICONS_DIRECTORY, BaseRti
from libargos.qt import QtGui
from libargos.utils.cls import (check_is_a_sequence, check_is_a_mapping, check_is_an_array,  
                                is_a_sequence, is_a_mapping, is_an_array, type_name)
from libargos.utils.misc import NOT_SPECIFIED

logger = logging.getLogger(__name__)

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
    """ Stores a Python or numpy scalar. 
        
        Is NOT sliceable and can not be inspected/plotted.
    """
    _iconOpen = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'memory.scalar.svg'))
    _iconClosed = _iconOpen      
    
    def __init__(self, scalar, nodeName='', fileName=''):
        super(ScalarRti, self).__init__(nodeName = nodeName, fileName=fileName)
        self._scalar = scalar 
    
    @property
    def elementTypeName(self):
        return type_name(self._scalar)
    
    def hasChildren(self):
        """ Returns False. Leaf nodes never have children. """
        return False
    
    

class FieldRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a field in a compound numpy array. 
    """ 
    _iconOpen = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'memory.field.svg'))
    _iconClosed = _iconOpen 
    
    def __init__(self, array, nodeName, fileName=''):
        """ Constructor.
            The name of the field must be given to the nodeName parameter. 
        """
        super(FieldRti, self).__init__(nodeName, fileName=fileName)
        check_is_an_array(array, allow_none=True)
        self._array = array
        

    def hasChildren(self):
        """ Returns False. Field nodes never have children. 
        """
        return False


    @property
    def isSliceable(self):
        """ Returns True because the underlying data can be sliced.
        """
        return True
    

    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
            Applies the index on the array that contain this field and then selects the
            current field. In pseudo-code, it returns: self.array[index][self.nodeName].
        """
        slicedArray = self._array.__getitem__(index)
        fieldName = self.nodeName
        return slicedArray[fieldName]


    @property
    def nDims(self):
        """ The number of dimensions of the underlying array
        """
        # Will only be called if self.isSliceable is True, so self._array will not be None
        return self._array.ndim


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
        """
        # Will only be called if self.isSliceable is True, so self._array will not be None
        return self._array.shape


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        if self._array is None:
            return super(FieldRti, self).elementTypeName
        else:
            fieldName = self.nodeName
            return str(self._array.dtype.fields[fieldName][0])



class ArrayRti(BaseRti):
    """ Represents a numpy array (or None for undefined)
    """
    _iconOpen = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'memory.array.svg'))
    _iconClosed = _iconOpen     

    def __init__(self, array, nodeName='', fileName=''):
        """ Constructor. 
            :param array: the underlying array. May be undefined (None)
            :type array: numpy.ndarray or None
        """
        super(ArrayRti, self).__init__(nodeName=nodeName, fileName=fileName)
        check_is_an_array(array, allow_none=True) # TODO: what about masked arrays?
        self._array = array

            
    def hasChildren(self):
        """ Returns True if the variable has a compound type, otherwise returns False.
        """
        return self._array is not None and bool(self._array.dtype.names)
           

    @property
    def isSliceable(self):
        """ Returns True if the underlying array is not None.
        """
        return self._array is not None


    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
            Passes the index through to the underlying array.
        """
        # Will only be called if self.isSliceable is True, so self._array will not be None
        return self._array.__getitem__(index)


    @property
    def nDims(self):
        """ The number of dimensions of the underlying array
        """
        # Will only be called if self.isSliceable is True, so self._array will not be None
        return self._array.ndim


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
        """
        # Will only be called if self.isSliceable is True, so self._array will not be None
        return self._array.shape


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        if self._array is None:
            return super(ArrayRti, self).elementTypeName 
        else:        
            dtype =  self._array.dtype
            return '<compound>' if dtype.names else str(dtype)


    def _fetchAllChildren(self):
        """ Fetches all fields that this variable contains. 
            Only variables with a compound data type can have fields.
        """        
        assert self.canFetchChildren(), "canFetchChildren must be True"

        childItems = []

        # Add fields in case of an array of compound type.
        if self.hasChildren():
            for fieldName in self._array.dtype.names:
                childItems.append(FieldRti(self._array, nodeName=fieldName,
                                           fileName=self.fileName))
        self._childrenFetched = True
        return childItems
    

class SequenceRti(BaseRti):
    """ Represents a sequence (e.g. a list or a tuple)
    """
    _iconOpen = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'memory.sequence.svg'))
    _iconClosed = _iconOpen     
    
    def __init__(self, sequence, nodeName='', fileName=''):
        """ Constructor. 
            :param sequence: the underlying sequence. May be undefined (None)
            :type array: None or a Python sequence (e.g. list or tuple)
        """
        super(SequenceRti, self).__init__(nodeName=nodeName, fileName=fileName)
        check_is_a_sequence(sequence, allow_none=True)
        self._sequence = sequence
        self._array = NOT_SPECIFIED # To cache the sequence converted to a numpy array.
   
    @property
    def _asArray(self):
        """ The sequence converted to a Numpy array. Returns None if the conversion fails
        """
        if self._array is NOT_SPECIFIED:
            try:
                self._array = np.array(self._sequence)
            except:
                self._array = None
        return self._array
    
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
    """ Represents a mapping (e.g. a dictionary)
    """    
    _iconOpen = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'memory.folder-open.svg'))
    _iconClosed = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'memory.folder-closed.svg'))
    
    def __init__(self, dictionary, nodeName='', fileName=''):
        """ Constructor
        """
        super(MappingRti, self).__init__(nodeName=nodeName, fileName=fileName)
        check_is_a_mapping(dictionary)
        self._dictionary = dictionary

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

