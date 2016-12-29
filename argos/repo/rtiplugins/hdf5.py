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

""" Repository Tree Items (RTIs) for HDF-5 data.

    It uses the h5py package to open HDF-5 files.
    See http://www.h5py.org/
"""

import logging, os
import h5py
import numpy as np


from argos.repo.iconfactory import RtiIconFactory
from argos.repo.baserti import BaseRti
from argos.utils.cls import to_string, check_class, is_an_array
from argos.utils.masks import maskedEqual

logger = logging.getLogger(__name__)

ICON_COLOR_H5PY = '#00EE88'


def dimNamesFromDataset(h5Dataset):
    """ Constructs the dimension names given a h5py dataset.

        First looks in the dataset's dimension scales to see if it refers to another
        dataset. In that case the referred dataset's name is used. If not, the label of the
        dimension scale is used. Finally, if this is empty, the dimension is numbered.
    """
    dimNames = [] # TODO: cache?
    for dimNr, dimScales in enumerate(h5Dataset.dims):
        if len(dimScales) == 0:
            dimNames.append('Dim{}'.format(dimNr))
        elif len(dimScales) == 1:
            dimScaleLabel, dimScaleDataset = dimScales.items()[0]
            path = dimScaleDataset.name
            if path:
                dimNames.append(os.path.basename(path))
            elif dimScaleLabel: # This could potentially be long so it's our second choice
                dimNames.append(dimScaleLabel)
            else:
                dimNames.append('Dim{}'.format(dimNr))
        else:
            # TODO: multiple scales for this dimension. What to do?
            logger.warn("More than one dimension scale found: {!r}".format(dimScales))
            dimNames.append('Dim{}'.format(dimNr)) # For now, just number them

    return dimNames


def dataSetElementType(h5Dataset):
    """ Returns a string describing the element type of the dataset
    """
    dtype =  h5Dataset.dtype

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


def dataSetUnit(h5Dataset):
    """ Returns the unit of the h5Dataset by looking in the attributes.

        It searches in the attributes for one of the following keys:
        'unit', 'units', 'Unit', 'Units', 'UNIT', 'UNITS'. If these are not found, the empty
        string is returned.

        Always returns a string
    """
    attributes = h5Dataset.attrs
    if not attributes:
        return '' # a premature optimization :-)

    for key in ('unit', 'units', 'Unit', 'Units', 'UNIT', 'UNITS'):
        if key in attributes:
            # In Python3 the attributes are byte strings so we must decode them
            # This a bug in h5py, see https://github.com/h5py/h5py/issues/379
            return to_string(attributes[key])
    # Not found
    return ''


def dataSetMissingValue(h5Dataset):
    """ Returns the missingData given a HDF-5 dataset

        Looks for one of the following attributes: _FillValue, missing_value, MissingValue,
        missingValue. Returns None if these attributes are not found.

        HDF-EOS and NetCDF files seem to put the attributes in 1-element arrays. So if the
        attribute contains an array of one element, that first element is returned here.
    """
    attributes = h5Dataset.attrs
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



class H5pyScalarRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a scalar HDF-5 variable.

    """
    _defaultIconGlyph = RtiIconFactory.SCALAR
    _defaultIconColor = ICON_COLOR_H5PY

    def __init__(self, h5Dataset, nodeName='', fileName=''):
        """ Constructor
        """
        super(H5pyScalarRti, self).__init__(nodeName = nodeName, fileName=fileName)
        check_class(h5Dataset, h5py.Dataset)
        self._h5Dataset = h5Dataset


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
        array = np.array([self._h5Dataset[()]]) # slice with empty tuple
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
        return dataSetElementType(self._h5Dataset)


    @property
    def attributes(self):
        """ The attributes dictionary.
        """
        return self._h5Dataset.attrs


    @property
    def unit(self):
        """ Returns the unit of the RTI by calling dataSetUnit on the underlying dataset
        """
        return dataSetUnit(self._h5Dataset)


    @property
    def missingDataValue(self):
        """ Returns the value to indicate missing data. None if no missing-data value is specified.
        """
        return dataSetMissingValue(self._h5Dataset)



class H5pyFieldRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a field in a structured HDF-5 variable.
    """
    _defaultIconGlyph = RtiIconFactory.FIELD
    _defaultIconColor = ICON_COLOR_H5PY

    def __init__(self, h5Dataset, nodeName, fileName=''):
        """ Constructor.
            The name of the field must be given to the nodeName parameter.
        """
        super(H5pyFieldRti, self).__init__(nodeName, fileName=fileName)
        check_class(h5Dataset, h5py.Dataset)
        self._h5Dataset = h5Dataset


    def hasChildren(self):
        """ Returns False. Field nodes never have children.
        """
        return False


    @property
    def attributes(self):
        """ The attributes dictionary.
            Returns the attributes of the variable that contains this field.
        """
        return self._h5Dataset.attrs


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
        mainArrayNumDims = len(self._h5Dataset.shape)
        mainIndex = index[:mainArrayNumDims]
        mainArray = self._h5Dataset.__getitem__(mainIndex)
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
        if self._h5Dataset.dtype.fields is None:
            return tuple() # regular field
        else:
            fieldName = self.nodeName
            fieldDtype = self._h5Dataset.dtype.fields[fieldName][0]
            return fieldDtype.shape


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
            If the field contains a subarray the shape may be longer than 1.
        """
        return self._h5Dataset.shape + self._subArrayShape


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        fieldName = self.nodeName
        return str(self._h5Dataset.dtype.fields[fieldName][0])


    @property
    def dimensionNames(self):
        """ Returns a list with the dimension names of the underlying NCDF variable
        """
        nSubDims = len(self._subArrayShape)
        subArrayDims = ['SubDim{}'.format(dimNr) for dimNr in range(nSubDims)]
        return dimNamesFromDataset(self._h5Dataset) + subArrayDims


    @property
    def unit(self):
        """ Returns the unit of the RTI by calling dataSetUnit on the underlying dataset
        """
        unit = dataSetUnit(self._h5Dataset)
        fieldNames = self._h5Dataset.dtype.names

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
        value = dataSetMissingValue(self._h5Dataset)
        fieldNames = self._h5Dataset.dtype.names

        # If the missing value attribute is a list with the same length as the number of fields,
        # return the missing value for field that equals the self.nodeName.
        if hasattr(value, '__len__') and len(value) == len(fieldNames):
            idx = fieldNames.index(self.nodeName)
            return value[idx]
        else:
            return value



class H5pyDatasetRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a HDF5 dataset.

        This includes dimenions scales, which are then displayed with a different icon.
    """
    #_defaultIconGlyph = RtiIconFactory.ARRAY # the iconGlyph property is overridden below
    _defaultIconColor = ICON_COLOR_H5PY

    def __init__(self, h5Dataset, nodeName, fileName=''):
        """ Constructor
        """
        super(H5pyDatasetRti, self).__init__(nodeName, fileName=fileName)
        check_class(h5Dataset, h5py.Dataset)
        self._h5Dataset = h5Dataset
        self._isStructured = bool(self._h5Dataset.dtype.names)


    @property
    def iconGlyph(self):
        """ Shows an Array icon for regular datasets but a dimension icon for dimension scales
        """
        if self._h5Dataset.attrs.get('CLASS', None) == b'DIMENSION_SCALE':
            return RtiIconFactory.DIMENSION
        else:
            return RtiIconFactory.ARRAY


    def hasChildren(self):
        """ Returns True if the variable has a structured type, otherwise returns False.
        """
        return self._isStructured


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
        return maskedEqual(self._h5Dataset.__getitem__(index), self.missingDataValue)


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
        """
        return self._h5Dataset.shape


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        return dataSetElementType(self._h5Dataset)


    @property
    def attributes(self):
        """ The attributes dictionary.
        """
        return self._h5Dataset.attrs


    @property
    def dimensionNames(self):
        """ Returns a list with the dimension names of the underlying HDF-5 dataset.
        """
        return dimNamesFromDataset(self._h5Dataset) # TODO: cache?


    @property
    def unit(self):
        """ Returns the unit of the RTI by calling dataSetUnit on the underlying dataset
        """
        return dataSetUnit(self._h5Dataset)


    @property
    def missingDataValue(self):
        """ Returns the value to indicate missing data. None if no missing-data value is specified.
        """
        return dataSetMissingValue(self._h5Dataset)


    def _fetchAllChildren(self):
        """ Fetches all fields that this variable contains.
            Only variables with a structured data type can have fields.
        """
        assert self.canFetchChildren(), "canFetchChildren must be True"

        childItems = []

        # Add fields
        if self._isStructured:
            for fieldName in self._h5Dataset.dtype.names:
                childItems.append(H5pyFieldRti(self._h5Dataset, nodeName=fieldName,
                                               fileName=self.fileName))

        return childItems


class H5pyGroupRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a HDF-5 group.
    """
    _defaultIconGlyph = RtiIconFactory.FOLDER
    _defaultIconColor = ICON_COLOR_H5PY

    def __init__(self, h5Group, nodeName, fileName=''):
        """ Constructor
        """
        super(H5pyGroupRti, self).__init__(nodeName, fileName=fileName)
        check_class(h5Group, h5py.Group, allow_none=True)

        self._h5Group = h5Group


    @property
    def attributes(self):
        """ The attributes dictionary.
        """
        return self._h5Group.attrs if self._h5Group else {}


    def _fetchAllChildren(self):
        """ Fetches all sub groups and variables that this group contains.
        """
        assert self._h5Group is not None, "dataset undefined (file not opened?)"
        assert self.canFetchChildren(), "canFetchChildren must be True"

        childItems = []

        for childName, h5Child in self._h5Group.items():
            if isinstance(h5Child, h5py.Group):
                childItems.append(H5pyGroupRti(h5Child, nodeName=childName,
                                               fileName=self.fileName))
            elif isinstance(h5Child, h5py.Dataset):
                if len(h5Child.shape) == 0:
                    childItems.append(H5pyScalarRti(h5Child, nodeName=childName,
                                                    fileName=self.fileName))
                else:
                    childItems.append(H5pyDatasetRti(h5Child, nodeName=childName,
                                                     fileName=self.fileName))

            elif isinstance(h5Child, h5py.Datatype):
                #logger.debug("Ignored DataType item: {}".format(childName))
                pass
            else:
                logger.warn("Ignored {}. It has an unexpected HDF-5 type: {}"
                            .format(childName, type(h5Child)))

        return childItems



class H5pyFileRti(H5pyGroupRti):
    """ Reads an HDF-5 file using the h5py package.

        See http://www.h5py.org/
    """
    _defaultIconGlyph = RtiIconFactory.FILE
    _defaultIconColor = ICON_COLOR_H5PY

    def __init__(self, nodeName, fileName=''):
        """ Constructor
        """
        super(H5pyFileRti, self).__init__(None, nodeName, fileName=fileName)
        self._checkFileExists()

    def _openResources(self):
        """ Opens the root Dataset.
        """
        logger.info("Opening: {}".format(self._fileName))
        self._h5Group = h5py.File(self._fileName, 'r')


    def _closeResources(self):
        """ Closes the root Dataset.
        """
        logger.info("Closing: {}".format(self._fileName))
        self._h5Group.close()
        self._h5Group = None
