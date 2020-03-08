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
import numpy as np
import yaml

from argos.repo.iconfactory import RtiIconFactory
from argos.repo.baserti import BaseRti
from argos.repo.filesytemrtis import createRtiFromFileName
from argos.utils.cls import to_string, check_class, is_an_array
from argos.utils.masks import maskedEqual


logger = logging.getLogger(__name__)

ICON_COLOR_EXDIR = '#FFBF00'
EXDIR_METADATA = 'exdir.yaml'
EXDIR_ATTRIBUTES = 'attributes.yaml'
EXDIR_DATA = 'data.npy'
EXDIR_VERSION = '1'


def dataSetElementType(dtype):
    """ Returns a string describing the element type of the dataset
    """

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


def dataSetUnit(exdirObj):
    """ Returns the unit of the exdirDataset by looking in the attributes.

        It searches in the attributes for one of the following keys:
        'unit', 'units', 'Unit', 'Units', 'UNIT', 'UNITS'. If these are not found, the empty
        string is returned.

        Always returns a string
    """
    attributes = exdirObj.attributes
    if not attributes:
        return '' # a premature optimization :-)

    for key in ('unit', 'units', 'Unit', 'Units', 'UNIT', 'UNITS'):
        if key in attributes:
            return attributes[key]
    # Not found
    return ''


def dataSetMissingValue(exdirObj):
    """ Returns the missingData given a Exdir dataset

        Looks for one of the following attributes: _FillValue, missing_value, MissingValue,
        missingValue. Returns None if these attributes are not found.
    """
    attributes = exdirObj.attributes
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
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flattenDict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def readYAMLFile(path):
    data = None
    try: 
        with open(path, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logger.warn(exc)
    except:
        pass
    return data


def metadataIsValid(metadata):
    isValid = False
    try:
        # checking metadata keys
        hasKey1 = 'exdir' in metadata
        hasKey2 = {'type', 'version'} == metadata['exdir'].keys()
        validType = {'file', 'group', 'dataset'} >= {metadata['exdir']['type']}
        
        # checking version
        validVersion = str(metadata['exdir']['version']) == EXDIR_VERSION
        
        isValid = hasKey1 and hasKey2 and validType and validVersion
    except:
        isValid = False
    return isValid


def isExdirType(exdirObj, typeName):
    isType = False
    try:
        metadataType = exdir.metadata['type'] 
        isType = metadataType == typeName
    except KeyError:
        isType = (typeName == 'Raw') or (typeName == 'raw')
    
    if not isType:
         raise TypeError("obj must be a of type {}, got: {}"
                         .format(typeName, str(metadataType)))


def getExdirTypeFromDir(dirPath):
    metadata = readYAMLFile(os.path.join(dirPath, EXDIR_METADATA))
    try:
        return metadata['exdir']['type']
    except:
        return ''


class ExdirObjRti(BaseRti):

    def __init__(self, parentObj, nodeName, fileName):
        """ Constructor
        """
        super(ExdirObjRti, self).__init__(nodeName, fileName=fileName)
        
        self.relativePath = nodeName if parentObj is None else os.path.join(
            parentObj.relativePath, nodeName)
        
        self._metadata = None
        self._attributes = None

    def loadMetadata(self):
        metadata = readYAMLFile(os.path.join(self.absPath, EXDIR_METADATA))
        if metadataIsValid(metadata):
            self._metadata = metadata
        else:
            self._metadata = {}

    def loadAttributes(self):
        attributes = readYAMLFile(os.path.join(self.absPath, EXDIR_ATTRIBUTES))
        if attributes is None or not isinstance(attributes, dict):
            self._attributes = {}
        else:
            self._attributes = attributes

    def getAllChildren(self, absPath=False):
        parentPath = self.absPath
        children = os.listdir(parentPath)
        if absPath:
            for i, c in enumerate(children):
                children[i] = os.path.join(parentPath, c)
        return children

    def getAllDirChildren(self, absPath=False):
        dirChildren = []
        for c in self.getAllChildren(absPath=False):
            childPath = os.path.join(self.absPath, c)
            if os.path.isdir(childPath):
                if absPath: 
                    dirChildren.append(childPath)
                else: 
                    dirChildren.append(c)
        return dirChildren
        
    @property
    def absPath(self):
        return os.path.abspath(self.relativePath)
    
    @property
    def attributes(self):
        """ The attributes dictionary.
        """
        if self._attributes is None:
            self.loadAttributes()
        return flattenDict(self._attributes) #flattenDict to remove nested dict

    @property
    def metadata(self):
    
        if self._metadata is None:
            self.loadMetadata()
        return self._metadata 



class ExdirDatasetRti(ExdirObjRti):
    """ Repository Tree Item (RTI) that contains an Exdir group.
    """
    _defaultIconGlyph = RtiIconFactory.ARRAY 
    _defaultIconColor = ICON_COLOR_EXDIR
    
    def __init__(self, parentObj, nodeName, fileName=''):
        """ Constructor
        """
        super(ExdirDatasetRti, self).__init__(parentObj, nodeName, fileName=fileName)
        # isExdirType(self, exdirType)

        self._data = None
        self._dataPath = os.path.join(self.absPath, EXDIR_DATA)
        self._hasRaws = len(self.getAllDirChildren()) > 0
    
    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
            Passes the index through to the underlying dataset.
            Converts to a masked array using the missing data value as fill_value
        """
        return maskedEqual(self.data.__getitem__(index), self.missingDataValue)

    def hasChildren(self):
        """ Returns True if the variable has a structured type or has Raw directories, 
            otherwise returns False.
        """
        return self._hasRaws

    @property
    def data(self):
        if self._data is None:
            self._data = np.load(self._dataPath, mmap_mode='r', allow_pickle=False)
        return self._data

    @property
    def isSliceable(self):
        """ Returns True because the underlying data can be sliced.
        """
        return True

    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
        """
        return self.data.shape

    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        return dataSetElementType(self.data.dtype)

    @property
    def unit(self):
        """ Returns the unit of the RTI by calling dataSetUnit on the underlying dataset
        """
        return dataSetUnit(self)

    @property
    def missingDataValue(self):
        """ Returns the value to indicate missing data. None if no missing-data value is specified.
        """
        return dataSetMissingValue(self)

    def _fetchAllChildren(self):
        """ Fetches all fields and raw dirs that this variable contains.
        """
        assert self.canFetchChildren(), "canFetchChildren must be True"

        childItems = []

        # Add raw directories
        if self._hasRaws:
            for fileName in self.getAllDirChildren():
                if not fileName.startswith('.'):
                    childItems.append(ExdirRawRti(self, fileName, self.fileName))

        return childItems


class ExdirRawRti(ExdirObjRti):
    """ Repository Tree Item (RTI) that contains an Exdir group.
    """
    _defaultIconGlyph = RtiIconFactory.FOLDER
    _defaultIconColor = ICON_COLOR_EXDIR 

    def __init__(self, parentObj, nodeName, fileName=''):
        """ Constructor
        """
        super(ExdirRawRti, self).__init__(parentObj, nodeName, fileName=fileName)


    def _fetchAllChildren(self):
        """ Fetches all sub groups and variables that this group contains.
        """
        assert self.canFetchChildren(), "canFetchChildren must be True"

        absPath = self.absPath
        allChildren = self.getAllChildren()
        
        childItems = []
        for child in allChildren:
            if not child.startswith('.'):
                childItem = createRtiFromFileName(os.path.join(absPath, child))
                childItems.append(childItem)

        return childItems


class ExdirGroupRti(ExdirObjRti):
    """ Repository Tree Item (RTI) that contains an Exdir group.
    """
    _defaultIconGlyph = RtiIconFactory.FOLDER
    _defaultIconColor = ICON_COLOR_EXDIR 

    def __init__(self, parentObj, nodeName, fileName=''):
        """ Constructor
        """
        super(ExdirGroupRti, self).__init__(parentObj, nodeName, fileName=fileName)
        # isExdirType(self, exdirType)


    def _fetchAllChildren(self):
        """ Fetches all sub groups and variables that this group contains.
        """
        assert self.canFetchChildren(), "canFetchChildren must be True"

        absPath = self.absPath
        allChildren = self.getAllDirChildren()

        childItems = []
        for child in allChildren:
            childAbsPath = os.path.join(absPath, child)
            
            childType = getExdirTypeFromDir(childAbsPath)

            if childType == 'group':
                childItems.append(ExdirGroupRti(self, nodeName=child, fileName=self.fileName))

            elif childType == 'dataset':
                childItems.append(ExdirDatasetRti(self, nodeName=child, fileName=self.fileName))

            elif childType == '':
                childItems.append(ExdirRawRti(self, nodeName=child, fileName=self.fileName))

            else:
                logger.warn("{} has an unexpected Exdir type."
                            .format(childName))
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

    def _closeResources(self):
        """ Closes the root Dataset.
        """
        logger.info("Closing: {}".format(self._fileName))

