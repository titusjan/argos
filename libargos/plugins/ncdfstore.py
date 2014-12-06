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

import logging
from netCDF4 import Dataset, Variable

from libargos.utils import check_class, type_name
from libargos.repo.abstractstore import (BaseRti, LazyLoadRtiMixin, 
                                             FileRtiMixin)

logger = logging.getLogger(__name__)


class VariableRti(BaseRti):

    def __init__(self, ncVar, nodeName=None):
        """ Constructor
        """
        super(VariableRti, self).__init__(nodeName = nodeName)
        check_class(ncVar, Variable)

        self._ncVar = ncVar
   
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
    
    

class DatasetRti(LazyLoadRtiMixin, BaseRti):

    def __init__(self, dataset, nodeName=None):
        """ Constructor
        """
        LazyLoadRtiMixin.__init__(self)
        BaseRti.__init__(self, nodeName=nodeName)
        check_class(dataset, Dataset)

        self._dataset = dataset
        self._childrenFetched = False

        
    def _fetchAllChildren(self):
        assert self.canFetchChildren(), "canFetchChildren must be True"
        
        childItems = []
        
        # Add groups
        for groupName, ncGroup in self._dataset.groups.items():
            childItems.append(DatasetRti(ncGroup, nodeName=groupName))
            
        # Add variables
        for varName, ncVar in self._dataset.variables.items():
            childItems.append(VariableRti(ncVar, nodeName=varName))
                        
        self._childrenFetched = True
        return childItems
    


class NcdfFileRti(FileRtiMixin, DatasetRti):
    """ Repository tree item that stores a netCDF file.
    """
    def __init__(self, fileName, nodeName=None):
        FileRtiMixin.__init__(self, fileName) 
        DatasetRti.__init__(self, Dataset(self._fileName), nodeName=nodeName)
  
    
    def closeFile(self):
        """ Closes the root Dataset.
        """
        self._dataset.close()
            
            
    