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

from libargos.utils import check_class, type_name
from libargos.selector.abstractstore import AbstractStore, GroupStoreTreeItem, StoreTreeItem

logger = logging.getLogger(__name__)


class VariableStroreTreeItem(StoreTreeItem):

    def __init__(self, store, ncVar, nodeName=None):
        """ Constructor
        """
        super(VariableStroreTreeItem, self).__init__(store, nodeName = nodeName)
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
    
    

class DatasetStoreTreeItem(GroupStoreTreeItem):

    def __init__(self, store, dataset, nodeName=None):
        """ Constructor
        """
        super(GroupStoreTreeItem, self).__init__(store, nodeName = nodeName)
        check_class(dataset, Dataset)

        self._dataset = dataset
        self._childrenFetched = False

        
    def fetchChildren(self):
        assert self.canFetchChildren(), "canFetchChildren must be True"
        childItems = []
        
        # Add groups
        for groupName, ncGroup in self._dataset.groups.items():
            childItems.append(DatasetStoreTreeItem(self.store, ncGroup, nodeName=groupName))
            
        # Add variables
        for varName, ncVar in self._dataset.variables.items():
            childItems.append(VariableStroreTreeItem(self.store, ncVar, nodeName=varName))
                        
        self._childrenFetched = True
        return childItems
    


class NcdfStore(AbstractStore):
    """ 
    """
    def __init__(self, fileName):
        super(NcdfStore, self).__init__()
        self._fileName = os.path.realpath(fileName)
        self._rootDataset = None
        
    @property
    def resourceNames(self):
        "Returns the name of the NCDF file"
        return self._fileName
        
    def isOpen(self):
        return self._rootDataset is not None
    
    def open(self):
        self._rootDataset = Dataset(self._fileName, 'r')
        
    def close(self):
        self._rootDataset.close()
        self._rootDataset = None
        
    @property
    def fileName(self):
        return self._fileName
    
    def createItems(self):
        """ Walks through all items and returns node to fill the repository
        """
        assert self.isOpen(), "File not opened: {}".format(self.fileName)
        
        fileRootItem = DatasetStoreTreeItem(self, self._rootDataset,  
                                            nodeName=os.path.basename(self.fileName))
        return fileRootItem


    
    