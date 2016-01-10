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

    They do implement a _closeResources() method that sets the references to the memory to None
    when the RTI is closed/deleted. This is perhaps not necessary but it might be possible that
    an RTI shares an object (indirectly) with its parent, causing a circular dependency. Setting
    the references to None breaks the cycle.

    The memory-RTIs store the attributes per-object instead of per-class.
"""
import logging, os

from .baserti import BaseRti
from libargos.repo.iconfactory import RtiIconFactory
from libargos.utils.cls import (check_is_a_sequence, check_is_a_mapping, check_is_an_array,  
                                is_a_sequence, is_a_mapping, is_an_array, type_name)
from libargos.utils.misc import NOT_SPECIFIED

logger = logging.getLogger(__name__)

def _createFromObject(obj, *args, **kwargs):
    """ Creates an RTI given an object. Auto-detects which RTI class to return.
        The *args and **kwargs parameters are passed to the RTI constructor.
        It is therefor important that all memory RTIs accept the same parameters in the
        constructor (with exception of the FieldRti which is not auto-detected).
    """
    if is_a_sequence(obj):
        return SequenceRti(obj, *args, **kwargs)
    elif is_a_mapping(obj):
        return MappingRti(obj, *args, **kwargs)
    elif is_an_array(obj):
        return ArrayRti(obj, *args, **kwargs)
    else:
        return ScalarRti(obj, *args, **kwargs)




class ScalarRti(BaseRti):
    """ Stores a Python or numpy scalar. 
        
        Is NOT sliceable and can not be inspected/plotted.
    """
    _defaultIconGlyph = RtiIconFactory.SCALAR
    _defaultIconColor = RtiIconFactory.COLOR_MEMORY

    def __init__(self, scalar, nodeName='', fileName='',
                 attributes=None, iconColor=_defaultIconColor):
        super(ScalarRti, self).__init__(nodeName = nodeName, fileName=fileName)
        self._scalar = scalar
        self._iconColor = iconColor
        self._attributes = {} if attributes is None else attributes


    def _closeResources(self):
        """ Sets the object references to None.
        """
        self._attributes = {}
        self._scalar = None


    @property
    def attributes(self):
        """ The attribute dictionary.
            Reimplemented from BaseRti: he attribute dictionary is stored per-object instead of
            per-class.
        """
        return self._attributes


    @property
    def elementTypeName(self):
        return type_name(self._scalar)


    def hasChildren(self):
        """ Returns False. Leaf nodes never have children. """
        return False
    
    

class FieldRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a field in a compound numpy array.
    """
    _defaultIconGlyph = RtiIconFactory.FIELD
    _defaultIconColor = RtiIconFactory.COLOR_MEMORY

    def __init__(self, array, nodeName, fileName='',
                 attributes=None, iconColor=_defaultIconColor):
        """ Constructor.
            The name of the field must be given to the nodeName parameter.
            The attributes can be set so the parent's attributes can be reused.
        """
        super(FieldRti, self).__init__(nodeName, fileName=fileName)
        check_is_an_array(array, allow_none=True)
        self._array = array
        self._iconColor = iconColor
        self._attributes = {} if attributes is None else attributes


    def _closeResources(self):
        """ Sets the object references to None.
        """
        self._attributes = {}
        self._array = None


    @property
    def attributes(self):
        """ The attribute dictionary.
            Reimplemented from BaseRti: he attribute dictionary is stored per-object instead of
            per-class.
        """
        return self._attributes
        

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
        logger.debug("FieldRti.__getitem__, index={!r}".format(index))
        fieldName = self.nodeName
        slicedArray = self._array[fieldName].__getitem__(index)
        return slicedArray


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
            If the field contains a subarray the shape may be longer than 1.
        """
        # Will only be called if self.isSliceable is True, so self._array will not be None
        if self._array.dtype.fields is None:
            return self._array.shape
        else:
            # The fields contains a sub-array.
            fieldName = self.nodeName
            fieldDtype = self._array.dtype.fields[fieldName][0]
            return self._array.shape + fieldDtype.shape


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
    """ Represents a numpy array (or None for undefined/unopened nodes)
    """
    _defaultIconGlyph = RtiIconFactory.ARRAY
    _defaultIconColor = RtiIconFactory.COLOR_MEMORY

    def __init__(self, array, nodeName='', fileName='',
                 attributes=None, iconColor=_defaultIconColor):
        """ Constructor. 
            :param array: the underlying array. May be undefined (None)
            :type array: numpy.ndarray or None
        """
        super(ArrayRti, self).__init__(nodeName=nodeName, fileName=fileName)
        check_is_an_array(array, allow_none=True) # TODO: what about masked arrays?
        self._array = array
        self._iconColor = iconColor
        self._attributes = {} if attributes is None else attributes


    def _closeResources(self):
        """ Sets the object references to None.
        """
        self._attributes = {}
        self._array = None


    @property
    def attributes(self):
        """ The attribute dictionary.
            Reimplemented from BaseRti: he attribute dictionary is stored per-object instead of
            per-class.
        """
        return self._attributes


    @property
    def isCompound(self):
        """ Returns True if the variable has a compound type, otherwise returns False.
        """
        return self._array is not None and bool(self._array.dtype.names)
           

    def hasChildren(self):
        """ Returns True if the variable has a compound type, otherwise returns False.
        """
        return self.isCompound

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
        if self.isCompound:
            for fieldName in self._array.dtype.names:
                childItem = FieldRti(self._array, nodeName=fieldName, fileName=self.fileName)
                childItems.append(childItem)

        #self._childrenFetched = True # TODO: necessary? (already done in ancestor?)
        return childItems
    

class SequenceRti(BaseRti):
    """ Represents a sequence (e.g. a list or a tuple).

        A sequence is always one-dimensional.
    """
    _defaultIconGlyph = RtiIconFactory.SEQUENCE
    _defaultIconColor = RtiIconFactory.COLOR_MEMORY
    
    def __init__(self, sequence, nodeName='', fileName='',
                 attributes=None, iconColor=_defaultIconColor):
        """ Constructor. 
            :param sequence: the underlying sequence. May be undefined (None)
            :type array: None or a Python sequence (e.g. list or tuple)
        """
        super(SequenceRti, self).__init__(nodeName=nodeName, fileName=fileName)
        check_is_a_sequence(sequence, allow_none=True)
        self._sequence = sequence
        #self._array = NOT_SPECIFIED # To cache the sequence converted to a numpy array.
        self._iconColor = iconColor
        self._attributes = {} if attributes is None else attributes


    def _closeResources(self):
        """ Sets the object references to None.
        """
        self._attributes = {}
        #self._array = NOT_SPECIFIED
        self._sequence = None


    @property
    def attributes(self):
        """ The attribute dictionary.
            Reimplemented from BaseRti: he attribute dictionary is stored per-object instead of
            per-class.
        """
        return self._attributes

    
    @property
    def typeName(self):
        return type_name(self._sequence)
    
        
    def _fetchAllChildren(self):
        """ Adds a child item for each column 
        """
        childItems = []
        for nr, elem in enumerate(self._sequence):
            childItem = _createFromObject(elem, "elem-{}".format(nr), self.fileName)
            childItem._iconColor = self.iconColor
            childItems.append(childItem)
        return childItems
    


class MappingRti(BaseRti):
    """ Represents a mapping (e.g. a dictionary)
    """
    _defaultIconGlyph = RtiIconFactory.FOLDER
    _defaultIconColor = RtiIconFactory.COLOR_MEMORY
    
    def __init__(self, dictionary, nodeName='', fileName='',
                 attributes=None, iconColor=_defaultIconColor):
        """ Constructor.
            The dictionary may be None for under(or None for undefined/unopened nodes)
        """
        super(MappingRti, self).__init__(nodeName=nodeName, fileName=fileName)
        check_is_a_mapping(dictionary, allow_none=True)
        self._dictionary = dictionary
        self._iconColor = iconColor
        self._attributes = {} if attributes is None else attributes


    def _closeResources(self):
        """ Sets the object references to None.
        """
        self._attributes = {}
        self._dictionary = None


    @property
    def attributes(self):
        """ The attribute dictionary.
            Reimplemented from BaseRti: he attribute dictionary is stored per-object instead of
            per-class.
        """
        return self._attributes


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        if self._dictionary is None:
            return super(MappingRti, self).elementTypeName
        else:
            return type_name(self._dictionary)


    def _fetchAllChildren(self):
        """ Adds a child item for each item 
        """        
        childItems = []
        logger.debug("{!r} _fetchAllChildren {!r}".format(self, self.fileName))

        if self.hasChildren():
            for key, value in sorted(self._dictionary.items()):
                # TODO: pass the attributes to the children? (probably not)
                childItem = _createFromObject(value, str(key), self.fileName)
                childItem._iconColor = self.iconColor
                childItems.append(childItem)
            
        return childItems
