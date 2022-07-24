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
from __future__ import absolute_import

import logging, os

import numpy as np
import h5py

from argos.repo.iconfactory import RtiIconFactory, ICON_COLOR_UNDEF
from argos.repo.baserti import BaseRti, shapeToSummary
from argos.utils.cls import to_string, check_class, is_an_array
from argos.utils.defs import DIM_TEMPLATE, SUB_DIM_TEMPLATE, CONTIGUOUS
from argos.utils.masks import maskedEqual
from argos.utils.moduleinfo import versionStrToTuple

logger = logging.getLogger(__name__)

H5PY_MAJOR_VERSION = versionStrToTuple(h5py.__version__)[0]
MAX_QUICK_LOOK_SIZE = 1000


def dimNamesFromDataset(h5Dataset, useBaseName=True):
    """ Constructs the dimension names given a h5py dataset.

        First looks in the dataset's dimension scales to see if it refers to another
        dataset. In that case the referred dataset's name is used. If not, the label of the
        dimension scale is used. Finally, if this is empty, the dimension is numbered.
    """
    dimNames = [] # TODO: cache?
    for dimNr, dimScales in enumerate(h5Dataset.dims):
        if len(dimScales) == 0:
            dimNames.append(DIM_TEMPLATE.format(dimNr))
        else:
            dimScaleLabel, dimScaleDataset = dimScales.items()[0]
            path = dimScaleDataset.name
            if path:
                dimName = os.path.basename(path) if useBaseName else path
            elif dimScaleLabel: # This could potentially be long so it's our second choice
                dimName = dimScaleLabel
            else:
                dimName = DIM_TEMPLATE.format(dimNr)

            if len(dimScales) > 1:
                logger.debug("More than one dimension scale found, using the first {}"
                             .format(dimName))

            dimNames.append(dimName)
        # else:
        #     # TODO: multiple scales for this dimension. What to do?
        #     dimNames.append(DIM_TEMPLATE.format(dimNr)) # For now, just number them

    return dimNames


def dataSetType(dtype, dimensionalityString):
    """ Returns a string describing the element type of the dataset.

        Args:
            dtype: numpy dtype of the dataset
            dimensionalityString: e.g. 'array ', 'scalar ', 'empty '
    """
    if dimensionalityString and dimensionalityString[0] != ' ':
        dimensionalityString = ' ' + dimensionalityString

    if dtype.names:
        return "compound{}".format(dimensionalityString)
    else:
        if H5PY_MAJOR_VERSION <= 2:
            # h5py version <= 2.x
            if dtype.metadata and 'vlen' in dtype.metadata:
                vlen_type = dtype.metadata['vlen']
                try:
                    return "<vlen {}>".format(vlen_type.__name__)  # when vlen_type is a type
                except AttributeError: #
                    return "<vlen {}>".format(vlen_type.name)      # when vlen_type is a dtype
        else:
            # h5py version >= 3.x
            stringInfo = h5py.check_string_dtype(dtype)
            if stringInfo is not None:
                # The dimensionality will be placed before the string encoding and length because
                # it's more important.
                if stringInfo.length is None:
                    return "string{} {} variable length"\
                        .format(dimensionalityString, stringInfo.encoding)
                else:
                    return "string{} {} length = {}"\
                        .format(dimensionalityString, stringInfo.encoding, stringInfo.length)

            vlenType = h5py.check_vlen_dtype(dtype)
            if vlenType is not None:
                # Note that, currently, variable length arrays cannot be displayed in any inspector!
                # In general, they cannot be loaded in a numpy array, only in some cases.
                # Therefore, they are hard to handle generically. Even the h5py documentation says
                # it's better to consider using something else if you've got the choice.
                # See: https://docs.h5py.org/en/stable/special.html#arbitrary-vlen-data
                return "{}{} variable length".format(vlenType, dimensionalityString)

    return "{}{}".format(dtype, dimensionalityString)



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


def attrsToDict(attrs):
    """ Converts attributes to a dictionary.

        In case an attribute can't be read and raises and exception, the attribute value will be
        the error message. This will make the attributes more robust.

        Necessary because, for instance, h5py may not be able to read all attributes
        generated by new versions of the Python netCDF4 library.
        # See: https://github.com/h5py/h5py/issues/719
    """
    result = {}
    for key in attrs.keys():
        try:
            result[key] = attrs[key]
        except Exception as ex:
            logger.warning("Unable to read {} attribute: {}".format(key, ex))
            result[key] = str(ex)
    return result


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


def _dataSetQuickLook(data, string_info):
    """ Makes a quick look representation of a dataset.

        Args:
            data: a numpy array or scalar
            string_info: h5py.string_dtype information read with h5py.check_string_dtype
    """
    if H5PY_MAJOR_VERSION <= 2:
        return str(data) # Just convert bytes to string in h5py <= 2.x
    else:
        if string_info is None:
            return str(data)  # not a string
        else:
            # Variable length (vlen) string datasets will yield a numpy array with object dtype.
            # First convert to a byte array so that we can decode it.
            bytesArray = np.char.asarray(data)
            return str(np.char.decode(bytesArray, encoding=string_info.encoding))



class H5pyScalarRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a scalar HDF-5 variable.

    """
    _defaultIconGlyph = RtiIconFactory.SCALAR

    def __init__(self, h5Dataset, nodeName='', fileName='', iconColor=ICON_COLOR_UNDEF):
        """ Constructor
        """
        super(H5pyScalarRti, self).__init__(
            nodeName=nodeName, fileName=fileName, iconColor=iconColor)
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
        return self._h5Dataset[()]


    @property
    def arrayShape(self):
        """ Returns the shape of the wrapper array. Will always be an empty tuple()
        """
        return tuple()


    @property
    def dimensionality(self):
        """ String that describes if the RTI is an array, scalar, field, etc.
        """
        return "empty" if self._h5Dataset.shape is None else "scalar"


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        return dataSetType(self._h5Dataset.dtype, '')


    @property
    def typeName(self):
        """ String representation of the type. By default, the elementTypeName + dimensionality.
        """
        return dataSetType(self._h5Dataset.dtype, self.dimensionality)


    @property
    def attributes(self):
        """ The attributes dictionary.
        """
        return attrsToDict(self._h5Dataset.attrs)


    @property
    def unit(self):
        """ Returns the unit of the RTI by calling dataSetUnit on the underlying dataset
        """
        return dataSetUnit(self._h5Dataset)


    @property
    def missingDataValue(self):
        """ Returns the value to indicate missing data. None if no missing-data value is specified.
        """
        # For empty datasets, self._h5Dataset.size can be None
        if self._h5Dataset.size is not None and self._h5Dataset.size > MAX_QUICK_LOOK_SIZE:
            return "{} of {}".format(self.typeName, self.summary)
        else:
            return dataSetMissingValue(self._h5Dataset)


    @property
    def summary(self):
        """ Returns a summary of the contents of the RTI. In this case the scalar as a string
        """
        if H5PY_MAJOR_VERSION <= 2:
            return str(self._h5Dataset[()])  # Just convert bytes to string in h5py <= 2.x
        else:
            # In h5py >= 3.x the encoding is known
            string_info = h5py.check_string_dtype(self._h5Dataset.dtype)

            if self._h5Dataset.shape is None:
                return "empty dataset"
            elif string_info is None:
                return str(self._h5Dataset[()])  # not a string
            else:
                return self._h5Dataset[()].decode(string_info.encoding, errors="replace")


    def quickLook(self, width: int):
        """ Returns a string representation fof the RTI to use in the Quik Look pane.

            Override default so bytes are decoded to strings.
        """
        return self.summary



class H5pyFieldRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a field in a structured HDF-5 variable.
    """
    _defaultIconGlyph = RtiIconFactory.FIELD

    def __init__(self, h5Dataset, nodeName, subArray, fileName='', iconColor=ICON_COLOR_UNDEF):
        """ Constructor.
        """
        super(H5pyFieldRti, self).__init__(nodeName, fileName=fileName, iconColor=iconColor)
        check_class(h5Dataset, h5py.Dataset)
        self._h5Dataset = h5Dataset

        self._subArray = subArray # The array that this field contains. Can be h5Dataset itself.
        self._isStructured = bool(self._subArray.dtype.names)


    def hasChildren(self):
        """ Returns False. Field nodes never have children.
        """
        return self._isStructured


    @property
    def attributes(self):
        """ The attributes dictionary.
            Returns the attributes of the variable that contains this field.
        """
        return attrsToDict(self._h5Dataset.attrs)


    @property
    def isSliceable(self):
        """ Returns True because the underlying data can be sliced.
        """
        return True


    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
            Applies the index on the HDF dataset that contain this field and then selects the
            current field. In pseudo-code, it returns: self.ncVar[index][self.nodeName].

            If the field itself contains a sub-array it returns:
                self.dataset[mainArrayIndex][self.nodeName][subArrayIndex]
        """
        return self._subArray[index]


    @property
    def nDims(self):
        """ The number of dimensions of the underlying array
        """
        return len(self.arrayShape) # h5py datasets don't have an ndim property


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
        """
        return self._subArray.shape


    @property
    def chunking(self):
        """ List with chunk sizes if chunked storage is used. Or 'contiguous' for contiguous storage
        """
        chunks = self._h5Dataset.chunks
        return CONTIGUOUS if chunks is None else chunks


    @property
    def dimensionality(self):
        """ String that describes if the RTI is an array, scalar, field, etc.
        """
        return "field"


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        return dataSetType(self._subArray.dtype, '')


    @property
    def typeName(self):
        """ String representation of the type. By default, the elementTypeName + dimensionality.
        """
        return dataSetType(self._subArray.dtype, self.dimensionality)


    @property
    def dimensionNames(self):
        """ Returns a list with the dimension names of the underlying HDF5 variable
        """
        nSubDims = len(self._subArray.shape)
        subArrayDims = [SUB_DIM_TEMPLATE.format(dimNr) for dimNr in range(nSubDims)]
        return dimNamesFromDataset(self._h5Dataset) + subArrayDims


    @property
    def dimensionPaths(self):
        """ Returns a list with the full path names of the dimensions.
        """
        nSubDims = len(self._subArray.shape)
        subArrayDims = [SUB_DIM_TEMPLATE.format(dimNr) for dimNr in range(nSubDims)]
        return dimNamesFromDataset(self._h5Dataset, useBaseName=False) + subArrayDims


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


    @property
    def summary(self):
        """ Returns a summary of the contents of the RTI.  E.g. 'array 20 x 30' elements.
        """
        return shapeToSummary(self.arrayShape)


    def quickLook(self, width: int):
        """ Returns a string representation fof the RTI to use in the Quik Look pane.
        """
        if self._h5Dataset.size > MAX_QUICK_LOOK_SIZE:
            return "{} of {}".format(self.typeName, self.summary)
        else:
            subIndex = tuple([Ellipsis])
            slicedArray = self._subArray[subIndex]
            data = maskedEqual(slicedArray, self.missingDataValue)

            string_info = h5py.check_string_dtype(self._h5Dataset.dtype)
            return _dataSetQuickLook(data, string_info)


    def _fetchAllChildren(self):
        """ Fetches all fields that this variable contains.
            Only variables with a structured data type can have fields.
        """
        assert self.canFetchChildren(), "canFetchChildren must be True"

        childItems = []
        if self._isStructured:
            for fieldName in self._subArray.dtype.names:
                childItems.append(H5pyFieldRti(
                    self._h5Dataset, fieldName, self._subArray[fieldName],
                    fileName=self.fileName, iconColor=self.iconColor))
        return childItems


class H5pyDatasetRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a HDF5 dataset.

        This includes dimenions scales, which are then displayed with a different icon.
    """
    #_defaultIconGlyph = RtiIconFactory.ARRAY # the iconGlyph property is overridden below

    def __init__(self, h5Dataset, nodeName, fileName='', iconColor=ICON_COLOR_UNDEF):
        """ Constructor
        """
        super(H5pyDatasetRti, self).__init__(nodeName, fileName=fileName, iconColor=iconColor)
        check_class(h5Dataset, h5py.Dataset)
        self._h5Dataset = h5Dataset
        self._isStructured = bool(self._h5Dataset.dtype.names)


    @property
    def iconGlyph(self):
        """ Shows an Array icon for regular datasets but a dimension icon for dimension scales
        """
        try:
            if self._h5Dataset.attrs.get('CLASS', None) == b'DIMENSION_SCALE':
                return RtiIconFactory.DIMENSION
            else:
                return RtiIconFactory.ARRAY
        except OSError as ex:
            logger.warning("Unable to read 'CLASS' attribute. Assuming regular dataset".format(ex))
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
        # Some old HDF5 files return bytes objects when containing string data. Convert to array.
        array = np.array(self._h5Dataset.__getitem__(index))
        return maskedEqual(array, self.missingDataValue)


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
        """
        return self._h5Dataset.shape


    @property
    def chunking(self):
        """ List with chunk sizes if chunked storage is used. Or 'contiguous' for contiguous storage
        """
        chunks = self._h5Dataset.chunks
        return CONTIGUOUS if chunks is None else chunks


    @property
    def dimensionality(self):
        """ String that describes if the RTI is an array, scalar, field, etc.
        """
        return "array"


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        return dataSetType(self._h5Dataset.dtype, '')


    @property
    def typeName(self):
        """ String representation of the type. By default, the elementTypeName + dimensionality.
        """
        return dataSetType(self._h5Dataset.dtype, self.dimensionality)


    @property
    def attributes(self):
        """ The attributes dictionary.
        """
        return attrsToDict(self._h5Dataset.attrs)


    @property
    def dimensionNames(self):
        """ Returns a list with the dimension names of the underlying HDF-5 dataset.
        """
        return dimNamesFromDataset(self._h5Dataset) # TODO: cache?


    @property
    def dimensionPaths(self):
        """ Returns a list with the full path names of the dimensions.
        """
        return dimNamesFromDataset(self._h5Dataset, useBaseName=False)


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


    @property
    def summary(self):
        """ Returns a summary of the contents of the RTI.  E.g. 'array 20 x 30' elements.
        """
        return shapeToSummary(self.arrayShape)


    def quickLook(self, width: int):
        """ Returns a string representation fof the RTI to use in the Quik Look pane.
        """
        if self._h5Dataset.size > MAX_QUICK_LOOK_SIZE:
            return "{} of {}".format(self.typeName, self.summary)
        else:
            data = maskedEqual(self._h5Dataset[:], self.missingDataValue)
            string_info = h5py.check_string_dtype(self._h5Dataset.dtype)
            return _dataSetQuickLook(data, string_info)


    def _fetchAllChildren(self):
        """ Fetches all fields that this variable contains.
            Only variables with a structured data type can have fields.
        """
        assert self.canFetchChildren(), "canFetchChildren must be True"

        childItems = []

        # Add fields
        if self._isStructured:
            for fieldName in self._h5Dataset.dtype.names:
                logger.critical("  dtype of {}: {}".format(fieldName, self._h5Dataset[fieldName].dtype))
                childItems.append(H5pyFieldRti(
                    self._h5Dataset, nodeName=fieldName, subArray=self._h5Dataset[fieldName],
                    fileName=self.fileName, iconColor=self.iconColor))
        return childItems


class H5pyGroupRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a HDF-5 group.
    """
    _defaultIconGlyph = RtiIconFactory.FOLDER

    def __init__(self, h5Group, nodeName, fileName='', iconColor=ICON_COLOR_UNDEF):
        """ Constructor
        """
        super(H5pyGroupRti, self).__init__(nodeName, fileName=fileName, iconColor=iconColor)
        check_class(h5Group, h5py.Group, allow_none=True)

        self._h5Group = h5Group


    @property
    def attributes(self):
        """ The attributes dictionary.
        """
        return attrsToDict(self._h5Group.attrs if self._h5Group else {})


    def _fetchAllChildren(self):
        """ Fetches all sub groups and variables that this group contains.
        """
        assert self._h5Group is not None, "dataset undefined (file not opened?)"
        assert self.canFetchChildren(), "canFetchChildren must be True"

        childItems = []

        for childName, h5Child in self._h5Group.items():
            if isinstance(h5Child, h5py.Group):
                childItems.append(H5pyGroupRti(
                    h5Child, nodeName=childName,
                    fileName=self.fileName, iconColor=self.iconColor))
            elif isinstance(h5Child, h5py.Dataset):
                # The shape can be None in case of Null datasets.
                if h5Child.shape is None or len(h5Child.shape) == 0:
                    childItems.append(H5pyScalarRti(
                        h5Child, nodeName=childName,
                        fileName=self.fileName, iconColor=self.iconColor))
                else:
                    childItems.append(H5pyDatasetRti(
                        h5Child, nodeName=childName,
                        fileName=self.fileName, iconColor=self.iconColor))

            elif isinstance(h5Child, h5py.Datatype):
                #logger.debug("Ignored DataType item: {}".format(childName))
                pass
            else:
                logger.warning("Ignored {}. It has an unexpected HDF-5 type: {}"
                            .format(childName, type(h5Child)))

        return childItems



class H5pyFileRti(H5pyGroupRti):
    """ Reads an HDF-5 file using the h5py package.

        See http://www.h5py.org/
    """
    _defaultIconGlyph = RtiIconFactory.FILE

    def __init__(self, nodeName, fileName='', iconColor=ICON_COLOR_UNDEF):
        """ Constructor
        """
        super(H5pyFileRti, self).__init__(None, nodeName, fileName=fileName, iconColor=iconColor)
        self._checkFileExists()

    def _openResources(self):
        """ Opens the root Dataset.
        """
        logger.info("Opening: {}".format(self._fileName))
        if not os.path.isfile(self._fileName):
            raise OSError("{} does not exist or is not a regular file.".format(self._fileName))
        self._h5Group = h5py.File(self._fileName, 'r')


    def _closeResources(self):
        """ Closes the root Dataset.
        """
        logger.info("Closing: {}".format(self._fileName))
        self._h5Group.close()
        self._h5Group = None
