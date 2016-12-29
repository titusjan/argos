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

""" Repository Tree Items (RTIs) for netCDF data.

    It uses the netCDF4 package to open netCDF files.
    See http://unidata.github.io/netcdf4-python/
"""

import logging, types
from netCDF4 import Dataset, Variable, Dimension

from argos.utils.cls import check_class
from argos.repo.baserti import BaseRti
from argos.repo.iconfactory import RtiIconFactory

logger = logging.getLogger(__name__)

ICON_COLOR_NCDF4 = '#0088FF'


def ncVarAttributes(ncVar):
    """ Returns the attributes of ncdf variable
    """
    try:
        return ncVar.__dict__
    except Exception as ex:
        # Due to some internal error netCDF4 may raise an AttributeError or KeyError,
        # depending on its version.
        logger.warn("Unable to read the attributes from {}. Reason: {}"
                    .format(ncVar.name, ex))
        return {}


def ncVarUnit(ncVar):
    """ Returns the unit of the ncVar by looking in the attributes.

        It searches in the attributes for one of the following keys:
        'unit', 'units', 'Unit', 'Units', 'UNIT', 'UNITS'. If these are not found, the empty
        string is returned.
    """
    attributes = ncVarAttributes(ncVar)
    if not attributes:
        return '' # a premature optimization :-)

    for key in ('unit', 'units', 'Unit', 'Units', 'UNIT', 'UNITS'):
        if key in attributes:
            # In Python3 the attribures are byte strings so we must decode them
            # This a bug in h5py, see https://github.com/h5py/h5py/issues/379
            return attributes[key]
    else:
        return ''



def variableMissingValue(ncVar):
    """ Returns the missingData given a NetCDF variable

        Looks for one of the following attributes: _FillValue, missing_value, MissingValue,
        missingValue. Returns None if these attributes are not found.
    """
    attributes = ncVarAttributes(ncVar)
    if not attributes:
        return None # a premature optimization :-)

    for key in ('missing_value', 'MissingValue', 'missingValue', 'FillValue', '_FillValue'):
        if key in attributes:
            missingDataValue = attributes[key]
            return missingDataValue
    return None



class NcdfDimensionRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a NCDF group.
    """
    _defaultIconGlyph = RtiIconFactory.DIMENSION
    _defaultIconColor = ICON_COLOR_NCDF4

    def __init__(self, ncDim, nodeName, fileName=''):
        """ Constructor
        """
        super(NcdfDimensionRti, self).__init__(nodeName, fileName=fileName)
        check_class(ncDim, Dimension)

        self._ncDim = ncDim

    def hasChildren(self):
        """ Returns False. Dimension items never have children.
        """
        return False

    @property
    def attributes(self):
        """ The attributes dictionary.
        """
        return {'unlimited': str(self._ncDim.isunlimited())}
        #size = self._ncDim.size
        #return {'size': 'unlimited' if size is None else str(size)}



class NcdfFieldRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a field in a structured NCDF variable.
    """
    _defaultIconGlyph = RtiIconFactory.FIELD
    _defaultIconColor = ICON_COLOR_NCDF4

    def __init__(self, ncVar, nodeName, fileName=''):
        """ Constructor.
            The name of the field must be given to the nodeName parameter.
        """
        super(NcdfFieldRti, self).__init__(nodeName, fileName=fileName)
        check_class(ncVar, Variable)

        self._ncVar = ncVar

    def hasChildren(self):
        """ Returns False. Field items never have children.
        """
        return False


    @property
    def isSliceable(self):
        """ Returns True because the underlying data can be sliced.
        """
        return True


    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
            Applies the index on the NCDF variable that contain this field and then selects the
            current field. In pseudo-code, it returns: self.h5Dataset[index][self.nodeName].

            If the field itself contains a sub-array it returns:
                self.h5Dataset[mainArrayIndex][self.nodeName][subArrayIndex]
        """
        mainArrayNumDims = self._ncVar.ndim
        mainIndex = index[:mainArrayNumDims]
        mainArray = self._ncVar.__getitem__(mainIndex)
        fieldArray = mainArray[self.nodeName]
        subIndex = tuple([Ellipsis]) + index[mainArrayNumDims:]
        slicedArray = fieldArray[subIndex]
        return slicedArray


    @property
    def nDims(self):
        """ The number of dimensions of the underlying array
        """
        return self._ncVar.ndim + len(self._subArrayShape)


    @property
    def _subArrayShape(self):
        """ Returns the shape of the sub-array
            An empty tuple is returned for regular fields, which have no sub array.
        """
        if self._ncVar.dtype.fields is None:
            return tuple() # regular field # TODO: does this occur?
        else:
            fieldName = self.nodeName
            fieldDtype = self._ncVar.dtype.fields[fieldName][0]
            return fieldDtype.shape


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
            If the field contains a subarray the shape may be longer than 1.
        """
        return self._ncVar.shape + self._subArrayShape


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        fieldName = self.nodeName
        return str(self._ncVar.dtype.fields[fieldName][0])


    @property
    def attributes(self):
        """ The attributes dictionary.
            Returns the attributes of the variable that contains this field.
        """
        return ncVarAttributes(self._ncVar)


    @property
    def unit(self):
        """ Returns the unit attribute of the underlying ncdf variable.

            If the units has a length (e.g is a list) and has precisely one element per field,
            the unit for this field is returned.
        """
        unit = ncVarUnit(self._ncVar)
        fieldNames = self._ncVar.dtype.names

        # If the missing value attribute is a list with the same length as the number of fields,
        # return the missing value for field that equals the self.nodeName.
        if hasattr(unit, '__len__') and len(unit) == len(fieldNames):
            idx = fieldNames.index(self.nodeName)
            return unit[idx]
        else:
            return unit



    @property
    def dimensionNames(self):
        """ Returns a list with the dimension names of the underlying NCDF variable
        """
        nSubDims = len(self._subArrayShape)
        subArrayDims = ['SubDim{}'.format(dimNr) for dimNr in range(nSubDims)]
        return list(self._ncVar.dimensions + tuple(subArrayDims))


    @property
    def missingDataValue(self):
        """ Returns the value to indicate missing data. None if no missing-data value is specified.
        """
        value = variableMissingValue(self._ncVar)
        fieldNames = self._ncVar.dtype.names

        # If the missing value attibute is a list with the same length as the number of fields,
        # return the missing value for field that equals the self.nodeName.
        if hasattr(value, '__len__') and len(value) == len(fieldNames):
            idx = fieldNames.index(self.nodeName)
            return value[idx]
        else:
            return value


class NcdfVariableRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a NCDF variable.
    """
    _defaultIconGlyph = RtiIconFactory.ARRAY
    _defaultIconColor = ICON_COLOR_NCDF4

    def __init__(self, ncVar, nodeName, fileName=''):
        """ Constructor
        """
        super(NcdfVariableRti, self).__init__(nodeName, fileName=fileName)
        check_class(ncVar, Variable)
        self._ncVar = ncVar

        try:
            self._isStructured = bool(self._ncVar.dtype.names)
        except (AttributeError, KeyError):
            # If dtype is a string instead of an numpy dtype, netCDF4 raises a KeyError
            # or AttributeError, depending on its version.
            self._isStructured = False

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
            Passes the index through to the underlying array.
        """
        return self._ncVar.__getitem__(index)


    @property
    def nDims(self):
        """ The number of dimensions of the underlying array
        """
        return self._ncVar.ndim


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
        """
        return self._ncVar.shape


    @property
    def attributes(self):
        """ The attributes dictionary.
            Returns the attributes of the variable that contains this field.
        """
        return ncVarAttributes(self._ncVar)


    @property
    def unit(self):
        """ Returns the unit attribute of the underlying ncdf variable
        """
        return ncVarUnit(self._ncVar)


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        dtype =  self._ncVar.dtype
        if type(dtype) == type:
            # Handle the unexpected case that dtype is a regular Python type
            # (happens e.g. in the /PROCESSOR/processing_configuration of the Trop LX files)
            return dtype.__name__

        return '<structured>' if dtype.names else str(dtype)


    @property
    def dimensionNames(self):
        """ Returns a list with the dimension names of the underlying NCDF variable
        """
        return self._ncVar.dimensions

#    TODO: how to get this?
#    @property
#    def dimensionGroupPaths(self):
#        """ Returns a list with, for every dimension, the path of the group that contains it.
#        """
#        return [dim.group().path for dim in self._ncVar.dimensions.values()] # TODO: cache?
#

    @property
    def missingDataValue(self):
        """ Returns the value to indicate missing data. None if no missing-data value is specified.
        """
        return variableMissingValue(self._ncVar)


    def _fetchAllChildren(self):
        """ Fetches all fields that this variable contains.
            Only variables with a structured data type can have fields.
        """
        assert self.canFetchChildren(), "canFetchChildren must be True"

        childItems = []

        # Add fields
        if self._isStructured:
            for fieldName in self._ncVar.dtype.names:
                childItems.append(NcdfFieldRti(self._ncVar, nodeName=fieldName, fileName=self.fileName))

        return childItems



class NcdfGroupRti(BaseRti):
    """ Repository Tree Item (RTI) that contains a NCDF group.
    """
    _defaultIconGlyph = RtiIconFactory.FOLDER
    _defaultIconColor = ICON_COLOR_NCDF4

    def __init__(self, ncGroup, nodeName, fileName=''):
        """ Constructor
        """
        super(NcdfGroupRti, self).__init__(nodeName, fileName=fileName)
        check_class(ncGroup, Dataset, allow_none=True)

        self._ncGroup = ncGroup


    @property
    def attributes(self):
        """ The attributes dictionary.
        """
        return self._ncGroup.__dict__ if self._ncGroup else {}


    def _fetchAllChildren(self):
        """ Fetches all sub groups and variables that this group contains.
        """
        assert self._ncGroup is not None, "dataset undefined (file not opened?)"
        assert self.canFetchChildren(), "canFetchChildren must be True"

        childItems = []

        # Add dimensions
        for dimName, ncDim in self._ncGroup.dimensions.items():
            childItems.append(NcdfDimensionRti(ncDim, nodeName=dimName, fileName=self.fileName))

        # Add groups
        for groupName, ncGroup in self._ncGroup.groups.items():
            childItems.append(NcdfGroupRti(ncGroup, nodeName=groupName, fileName=self.fileName))

        # Add variables
        for varName, ncVar in self._ncGroup.variables.items():
            childItems.append(NcdfVariableRti(ncVar, nodeName=varName, fileName=self.fileName))

        return childItems



class NcdfFileRti(NcdfGroupRti):
    """ Reads a NetCDF file using the netCDF4 module.

        See http://unidata.github.io/netcdf4-python/
    """
    _defaultIconGlyph = RtiIconFactory.FILE
    _defaultIconColor = ICON_COLOR_NCDF4

    def __init__(self, nodeName, fileName=''):
        """ Constructor
        """
        super(NcdfFileRti, self).__init__(None, nodeName, fileName=fileName)
        self._checkFileExists()

    def _openResources(self):
        """ Opens the root Dataset.
        """
        logger.info("Opening: {}".format(self._fileName))
        self._ncGroup = Dataset(self._fileName)

    def _closeResources(self):
        """ Closes the root Dataset.
        """
        logger.info("Closing: {}".format(self._fileName))
        self._ncGroup.close()
        self._ncGroup = None
