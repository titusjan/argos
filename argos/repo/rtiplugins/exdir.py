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

""" Repository Tree Items (RTIs) for Exdir data.

"""

import logging, os
import collections
import exdir
import numpy as np

from argos.repo.iconfactory import RtiIconFactory
from argos.repo.baserti import BaseRti
from argos.repo.filesytemrtis import createRtiFromFileName
from argos.utils.cls import to_string, check_class, is_an_array
from argos.utils.masks import maskedEqual


logger = logging.getLogger(__name__)

ICON_COLOR_EXDIR = '#00BBFF'


def dataSetElementType(exdirDataset):
    """ Returns a string describing the element type of the dataset
    """
    dtype =  exdirDataset.dtype

    if dtype.names:
        return '<structured>'
    else:
        if dtype.metadata and 'vlen' in dtype.metadata:
            vlen_type = dtype.metadata['vlen']
            try:
                return "<vlen {}>".format(vlen_type.__name__)  # when vlen_type is a type
            except AttributeError: #
                return "<vlen {}>".format(vlen_type.name)      # when vlen_type is a dtype

    return str(dtype)


def dataSetUnit(exdirDataset):
    """ Returns the unit of the exdirDataset by looking in the attributes.

        It searches in the attributes for one of the following keys:
        'unit', 'units', 'Unit', 'Units', 'UNIT', 'UNITS'. If these are not found, the empty
        string is returned.

        Always returns a string
    """
    attributes = exdirDataset.attrs.to_dict()
    if not attributes:
        return '' # a premature optimization :-)

    for key in ('unit', 'units', 'Unit', 'Units', 'UNIT', 'UNITS'):
        if key in attributes:
            return attributes[key]
    # Not found
    return ''


def dataSetMissingValue(exdirDataset):
    """ Returns the missingData given a Exdir dataset

        Looks for one of the following attributes: _FillValue, missing_value, MissingValue,
        missingValue. Returns None if these attributes are not found.
    """
    attributes = exdirDataset.attrs.to_dict()
    if not attributes:
        return None # a premature optimization :-)

    for key in ('missing_value', 'MissingValue', 'missingValue', 'FillValue', '_FillValue'):
        if key in attributes:
            missingDataValue = attributes[key]
            if is_an_array(missingDataValue) and len(missingDataValue) == 1:
                return missingDataValue[0] # In case of HDF-EOS and NetCDF files
            else:
                return missingDataValue
    return None


def flattenDict(d, parent_key='', sep='/'):
    """ Returns a flatten dictionary given a nested dictionary. 

        The nested keys are be separated by sep. 
    """
    items = []
    if isinstance(d,list): d = {str(i) : v for i, v in enumerate(d)} 
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flattenDict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)



class ExdirScalarRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a scalar HDF-5 variable.

    """
    _defaultIconGlyph = RtiIconFactory.SCALAR
    _defaultIconColor = ICON_COLOR_EXDIR

    def __init__(self, exdirDataset, nodeName='', fileName=''):
        """ Constructor
        """
        super(ExdirScalarRti, self).__init__(nodeName = nodeName, fileName=fileName)
        check_class(exdirDataset, exdir.Dataset)
        self._exdirDataset = exdirDataset


    def hasChildren(self):
        """ Returns False. Leaf nodes never have children. """
        return False


    @property
    def isSliceable(self):
        """ Returns True because the underlying data can be sliced.
            The scalar will be wrapped in an array with one element so it can be inspected.
        """
        return True


    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
            The scalar will be wrapped in an array with one element so it can be inspected.
        """
        array = np.array([self._exdirDataset[()]]) # slice with empty tuple
        maskedArray = maskedEqual(array, self.missingDataValue)

        assert maskedArray.shape == (1, ), "Scalar wrapper shape mismatch: {}".format(array.shape)
        return maskedArray[index] # Use the index to ensure the slice has the correct shape


    @property
    def arrayShape(self):
        """ Returns the shape of the wrapper array. Will always be the tuple (1, )
        """
        return (1, )


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        return dataSetElementType(self._exdirDataset)


    @property
    def attributes(self):
        """ The attributes dictionary.
        """
        return flattenDict(self._exdirDataset.attrs.to_dict()) # add to_dict() ?


    @property
    def unit(self):
        """ Returns the unit of the RTI by calling dataSetUnit on the underlying dataset
        """
        return dataSetUnit(self._exdirDataset)


    @property
    def missingDataValue(self):
        """ Returns the value to indicate missing data. None if no missing-data value is specified.
        """
        return dataSetMissingValue(self._exdirDataset)


class ExdirFieldRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a field in a structured HDF-5 variable.
    """
    _defaultIconGlyph = RtiIconFactory.FIELD
    _defaultIconColor = ICON_COLOR_EXDIR

    def __init__(self, exdirDataset, nodeName, fileName=''):
        """ Constructor.
            The name of the field must be given to the nodeName parameter.
        """
        super(ExdirFieldRti, self).__init__(nodeName, fileName=fileName)
        check_class(exdirDataset, exdir.Dataset)
        self._exdirDataset = exdirDataset


    def hasChildren(self):
        """ Returns False. Field nodes never have children.
        """
        return False


    @property
    def attributes(self):
        """ The attributes dictionary.
            Returns the attributes of the variable that contains this field.
        """
        return flattenDict(self._exdirDataset.attrs.to_dict()) # add to_dict() ?


    @property
    def isSliceable(self):
        """ Returns True because the underlying data can be sliced.
        """
        return True


    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
            Applies the index on the NCDF variable that contain this field and then selects the
            current field. In pseudo-code, it returns: self.ncVar[index][self.nodeName].

            If the field itself contains a sub-array it returns:
                self.ncVar[mainArrayIndex][self.nodeName][subArrayIndex]
        """
        mainArrayNumDims = len(self._exdirDataset.shape)
        mainIndex = index[:mainArrayNumDims]
        mainArray = self._exdirDataset.__getitem__(mainIndex)
        fieldArray = mainArray[self.nodeName]
        subIndex = tuple([Ellipsis]) + index[mainArrayNumDims:]
        slicedArray = fieldArray[subIndex]

        return maskedEqual(slicedArray, self.missingDataValue)


    @property
    def nDims(self):
        """ The number of dimensions of the underlying array
        """
        return len(self.arrayShape) # h5py datasets don't have an ndim property


    @property
    def _subArrayShape(self):
        """ Returns the shape of the sub-array
            An empty tuple is returned for regular fields, which have no sub array.
        """
        if self._exdirDataset.dtype.fields is None:
            return tuple() # regular field
        else:
            fieldName = self.nodeName
            fieldDtype = self._exdirDataset.dtype.fields[fieldName][0]
            return fieldDtype.shape


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
            If the field contains a subarray the shape may be longer than 1.
        """
        return self._exdirDataset.shape + self._subArrayShape


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        fieldName = self.nodeName
        return str(self._exdirDataset.dtype.fields[fieldName][0])


    @property
    def dimensionNames(self):
        """ Returns a list with the dimension names of the underlying NCDF variable
        """
        nSubDims = len(self._subArrayShape)
        subArrayDims = ['SubDim{}'.format(dimNr) for dimNr in range(nSubDims)]
        return dimNamesFromDataset(self._exdirDataset) + subArrayDims


    @property
    def unit(self):
        """ Returns the unit of the RTI by calling dataSetUnit on the underlying dataset
        """
        unit = dataSetUnit(self._exdirDataset)
        fieldNames = self._exdirDataset.dtype.names

        # If the missing value attribute is a list with the same length as the number of fields,
        # return the missing value for field that equals the self.nodeName.
        if hasattr(unit, '__len__') and len(unit) == len(fieldNames):
            idx = fieldNames.index(self.nodeName)
            return unit[idx]
        else:
            return unit


    @property
    def missingDataValue(self):
        """ Returns the value to indicate missing data. None if no missing-data value is specified.
        """
        value = dataSetMissingValue(self._exdirDataset)
        fieldNames = self._exdirDataset.dtype.names

        # If the missing value attribute is a list with the same length as the number of fields,
        # return the missing value for field that equals the self.nodeName.
        if hasattr(value, '__len__') and len(value) == len(fieldNames):
            idx = fieldNames.index(self.nodeName)
            return value[idx]
        else:
            return value


class ExdirDatasetRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a HDF5 dataset.

        This includes dimenions scales, which are then displayed with a different icon.
    """
    _defaultIconGlyph = RtiIconFactory.ARRAY # the iconGlyph property is overridden below
    _defaultIconColor = ICON_COLOR_EXDIR

    def __init__(self, exdirDataset, nodeName, fileName=''):
        """ Constructor
        """
        super(ExdirDatasetRti, self).__init__(nodeName, fileName=fileName)
        check_class(exdirDataset, exdir.Dataset)
        self._exdirDataset = exdirDataset
        self._isStructured = bool(self._exdirDataset.dtype.names)


        fileNames = os.listdir(os.path.abspath(self._exdirDataset.directory))
        absFileNames = [os.path.join(self._exdirDataset.directory, fn) for fn in fileNames]
        self._hasRaws = sum([os.path.isdir(f) for f in absFileNames]) > 0

    def hasChildren(self):
        """ Returns True if the variable has a structured type, otherwise returns False.
        """
        return self._isStructured or self._hasRaws


    @property
    def isSliceable(self):
        """ Returns True because the underlying data can be sliced.
        """
        return True


    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
            Passes the index through to the underlying dataset.
            Converts to a masked array using the missing data value as fill_value
        """
        return maskedEqual(self._exdirDataset.__getitem__(index), self.missingDataValue)


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
        """
        return self._exdirDataset.shape


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        return dataSetElementType(self._exdirDataset)


    @property
    def attributes(self):
        """ The attributes dictionary.
        """
        return flattenDict(self._exdirDataset.attrs.to_dict()) #add .to_dict() ?


    @property
    def unit(self):
        """ Returns the unit of the RTI by calling dataSetUnit on the underlying dataset
        """
        return dataSetUnit(self._exdirDataset)


    @property
    def missingDataValue(self):
        """ Returns the value to indicate missing data. None if no missing-data value is specified.
        """
        return dataSetMissingValue(self._exdirDataset)


    def _fetchAllChildren(self):
        """ Fetches all fields that this variable contains.
            Only variables with a structured data type can have fields.
        """
        assert self.canFetchChildren(), "canFetchChildren must be True"

        childItems = []

        # Add fields
        if self._isStructured:
            for fieldName in self._exdirDataset.dtype.names:
                childItems.append(ExdirFieldRti(self._exdirDataset, nodeName=fieldName,
                                               fileName=self.fileName))


        # Add raw directories
        if self._hasRaws:
            fileNames = os.listdir(os.path.abspath(self._exdirDataset.directory))
            absFileNames = [os.path.join(self._exdirDataset.directory, fn) for fn in fileNames]

            for fileName, absFileName in zip(fileNames, absFileNames):
                if os.path.isdir(absFileName) and not fileName.startswith('.'):
                    childItems.append(ExdirRawRti(self._exdirDataset.require_raw(fileName), nodeName=fileName,
                                                    fileName=self.fileName))



        return childItems


class ExdirRawRti(BaseRti):
    """ Repository Tree Item (RTI) that contains an Exdir Raw.
    """
    _defaultIconGlyph = RtiIconFactory.FOLDER
    _defaultIconColor = ICON_COLOR_EXDIR

    def __init__(self, exdirRaw, nodeName, fileName=''):
        """ Constructor
        """
        super(ExdirRawRti, self).__init__(nodeName, fileName=fileName)
        check_class(exdirRaw, exdir.Raw, allow_none=True)

        self._exdirRaw = exdirRaw


    def _fetchAllChildren(self): # Raw is treated like a directory
        """ Fetches all sub groups and variables that this group contains.
        """
        assert self._exdirRaw is not None, "dataset undefined (file not opened?)"
        assert self.canFetchChildren(), "canFetchChildren must be True"

        childItems = []

        absPaths = os.path.abspath(self._exdirRaw.directory)
        fileNames = os.listdir(absPaths)
        absFileNames = [os.path.join(self._exdirRaw.directory, fn) for fn in fileNames]

        for fileName, absFileName in zip(fileNames, absFileNames):
            if not fileName.startswith('.'):
                childItem = createRtiFromFileName(absFileName)
                childItems.append(childItem)

        return childItems


class ExdirGroupRti(BaseRti):
    """ Repository Tree Item (RTI) that contains an Exdir group.
    """
    _defaultIconGlyph = RtiIconFactory.FOLDER
    _defaultIconColor = ICON_COLOR_EXDIR

    def __init__(self, exdirGroup, nodeName, fileName=''):
        """ Constructor
        """
        super(ExdirGroupRti, self).__init__(nodeName, fileName=fileName)
        check_class(exdirGroup, exdir.Group, allow_none=True)

        self._exdirGroup = exdirGroup


    @property
    def attributes(self):
        """ The attributes dictionary.
        """
        return flattenDict(self._exdirGroup.attrs.to_dict()) if self._exdirGroup else {}


    def _fetchAllChildren(self):
        """ Fetches all sub groups and variables that this group contains.
        """
        assert self._exdirGroup is not None, "dataset undefined (file not opened?)"
        assert self.canFetchChildren(), "canFetchChildren must be True"

        childItems = []

        for childName, exdirChild in self._exdirGroup.items():
            if isinstance(exdirChild, exdir.Group):
                childItems.append(ExdirGroupRti(exdirChild, nodeName=childName,
                                               fileName=self.fileName))

            elif isinstance(exdirChild, exdir.Raw):
                childItems.append(ExdirRawRti(exdirChild, nodeName=childName,
                                               fileName=self.fileName))
            
            elif isinstance(exdirChild, exdir.Dataset):
                if len(exdirChild.shape) == 0:
                    childItems.append(ExdirScalarRti(exdirChild, nodeName=childName,
                                                    fileName=self.fileName))
                else:
                    childItems.append(ExdirDatasetRti(exdirChild, nodeName=childName,
                                                     fileName=self.fileName))
            else:
                logger.warn("Ignored {}. It has an unexpected Exdir type: {}"
                            .format(childName, type(exdir)))

        return childItems


class ExdirFileRti(ExdirGroupRti):
    """ Reads an Exdir file using the exdir package.
    """
    _defaultIconGlyph = RtiIconFactory.FILE
    _defaultIconColor = ICON_COLOR_EXDIR

    def __init__(self, nodeName, fileName=''):
        """ Constructor
        """
        super(ExdirFileRti, self).__init__(None, nodeName, fileName=fileName)
        self._checkFileExists()

    def _openResources(self):
        """ Opens the root Dataset.
        """
        logger.info("Opening: {}".format(self._fileName))
        self._exdirGroup = exdir.File(self._fileName)


    def _closeResources(self):
        """ Closes the root Dataset.
        """
        logger.info("Closing: {}".format(self._fileName))
        self._exdirGroup.close()
        self._exdirGroup = None