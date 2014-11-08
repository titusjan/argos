#from .wrappers import BaseWrapper
import logging, os
import numpy as np

from libargos.selector.storeitems import StoreGroupTreeItem, StoreArrayTreeItem

logger = logging.getLogger(__name__)


class AbstractDataStore(object):
    
    def open(self, fileName):
        pass
    
    def close(self):
        pass
    
    def createItems(self):
        """ Walks through all items and returns node to fill the repository
        """
        pass

#
#class MemoryStore(AbstractDataStore):
#    
#    def open(self, fileName):
#        pass
#    
#    def close(self):
#        pass
#    
#    def createItems(self):
#        """ Walks through all items and returns node to fill the repository
#        """
#        pass


class SimpleTextFileStore(AbstractDataStore):
    """ 
    """
    
    def __init__(self, fileName):
        self._fileName = fileName
        self._data2D = None
    
    def open(self):
        self._data2D = np.loadtxt(self.fileName, ndmin=0)
    
    def close(self):
        self._data2D = None
        
    
    @property
    def fileName(self):
        return self._fileName
            
    
    def createItems(self):
        """ Walks through all items and returns node to fill the repository
        """
        assert self._data2D is not None, "File not opened: {}".format(self.fileName)
        
        fileRootItem = StoreGroupTreeItem(parentItem=None, 
                                          nodeName=os.path.basename(self.fileName), 
                                          nodeId=self.fileName)
        _nRows, nCols = self._data2D.shape
        for col in range(nCols):
            colItem = StoreArrayTreeItem(self._data2D[:,col], nodeName="column {}".format(col))
            fileRootItem.insertItem(colItem)
            
        return fileRootItem


    
    