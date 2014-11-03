

from libargos.utils import check_class
from libargos.qt import QtGui, QtCore
from libargos.qt.editabletreemodel import BaseTreeModel, BaseTreeItem



class ScalarTreeItem(BaseTreeItem):
    
    def __init__(self, name, value, parentItem=None):
        super(ScalarTreeItem, self).__init__(parentItem)
        self.name = name
        self.value = value 


  
    

class RepositoryTreeModel(BaseTreeModel):
    """ The main entry point of all the data
    
        Maintains a list of open files and offers a QAbstractItemModel for read-only access of
        the data with QTreeViews.
    """
    
    def __init__(self, parent=None):
        """ Constructor
        """
        super(RepositoryTreeModel, self).__init__(headers=["name", "value"], parent=parent)
        

    def addScalar(self, name, value, position=None, parentIndex=QtCore.QModelIndex()):
        
        childItem = ScalarTreeItem(name, value)
        childIndex = self.insertChild(childItem, position, parentIndex)
        return childIndex

    
    def _itemValueForColumn(self, treeItem, column):
        """ Returns the value of the item given the column number
        """
        if column == 0:
            return treeItem.name
        elif column == 1:
            return treeItem.value
        else:
            raise ValueError("Invalid column: {}".format(column))

        
# Making a separate class instead of inheriting form BaseTreeModel/AbstractItemModel 
# as to keep the interface small.
   
class Repository(object):
    """ Keeps a list of stores (generally open files) and allows for adding and removing them.
    """
    
    def __init__(self):
        
        self.stores = []
        self.treeModel = RepositoryTreeModel()
        
    
    def addStore(self, store):
        pass
        
    