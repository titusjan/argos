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

""" Data store for netCDF data.

    It uses the netCDF4 package to open netCDF files.
    See http://unidata.github.io/netcdf4-python/
"""

import logging, os
from netCDF4 import Dataset, Variable

from libargos.qt import QtGui
from libargos.utils.cls import check_class, type_name
from libargos.repo.baserti import (ICONS_DIRECTORY, BaseRti)

logger = logging.getLogger(__name__)


class VariableRti(BaseRti):

    _label = "NCDF Variable"
    _iconOpen = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'ncdf.variable.svg'))
    _iconClosed = _iconOpen 
    
    def __init__(self, ncVar, nodeName='', fileName=''):
        """ Constructor
        """
        super(VariableRti, self).__init__(nodeName = nodeName, fileName=fileName)
        check_class(ncVar, Variable)

        self._ncVar = ncVar
        
#    def canFetchChildren(self):
#        return False
            
    def hasChildren(self):
        """ Returns False. Leaf nodes never have children. """
        return False
   
    @property
    def attributes(self):
        return self._ncVar.__dict__

    @property
    def arrayShape(self):
        return self._ncVar.shape

    @property
    def typeName(self):
        return type_name(self._ncVar)
    
    @property
    def elementTypeName(self):
        dtype =  self._ncVar.dtype
        return '<compound>' if dtype.names else str(dtype)
    
    

class DatasetRti(BaseRti): # TODO: rename to GroupRti?

    _label = "NCDF Group"
    _iconClosed = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'ncdf.group-closed.svg'))
    _iconOpen = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'ncdf.group-open.svg'))
    
    def __init__(self, dataset, nodeName='', fileName=''):
        """ Constructor
        """
        super(DatasetRti, self).__init__(nodeName=nodeName, fileName=fileName)
        check_class(dataset, Dataset, allow_none=True)

        self._dataset = dataset
        self._childrenFetched = False
        
    @property
    def attributes(self):
        return self._dataset.__dict__ if self._dataset else {}
        
               
    def _fetchAllChildren(self):
        assert self._dataset is not None, "dataset undefined (file not opened?)"
        assert self.canFetchChildren(), "canFetchChildren must be True"
        
        childItems = []
        
        # Add groups
        for groupName, ncGroup in self._dataset.groups.items():
            childItems.append(DatasetRti(ncGroup, nodeName=groupName, fileName=self.fileName))
            
        # Add variables
        for varName, ncVar in self._dataset.variables.items():
            childItems.append(VariableRti(ncVar, nodeName=varName, fileName=self.fileName))
                        
        self._childrenFetched = True
        return childItems
    


class NcdfFileRti(DatasetRti):
    """ Repository tree item that stores a netCDF file.
    """
    _label = "NCDF File"
    _iconClosed = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'ncdf.file-closed.svg'))
    _iconOpen = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'ncdf.file-open.svg'))
        
    def __init__(self, nodeName='', fileName=''):
        """ Constructor
        """
        super(NcdfFileRti, self).__init__(None, nodeName=nodeName, fileName=fileName)
        self._checkFileExists()
        
    @property
    def attributes(self):
        return self._dataset.__dict__ if self._dataset else {}
    
    def _openResources(self):
        """ Opens the root Dataset.
        """
        logger.info("Opening: {}".format(self._fileName))
        self._dataset = Dataset(self._fileName)
    
    def _closeResources(self):
        """ Closes the root Dataset.
        """
        logger.info("Closing: {}".format(self._fileName))
        self._dataset.close()
        self._dataset = None
