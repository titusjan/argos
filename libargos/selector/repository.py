

from libargos.qt import QtGui, QtCore
from libargos.qt.editabletreemodel import BaseTreeModel
from libargos.selector.storeitems import StoreScalarTreeItem
from libargos.info import DEBUGGING
#from libargos.utils import check_class

    

class RepositoryTreeModel(BaseTreeModel):
    """ The main entry point of all the data
    
        Maintains a list of open files and offers a QAbstractItemModel for read-only access of
        the data with QTreeViews.
    """
    def __init__(self, parent=None):
        """ Constructor
        """
        headers = ["name", "value", "shape", "type"]
        super(RepositoryTreeModel, self).__init__(headers=headers, parent=parent)
        self._isEditable = False


    def flags(self, index):
        """ Returns the item flags for the given index.
        """
        if not index.isValid():
            return 0
        
        if index.column() == 1:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        
        
    def addScalar(self, name, value, position=None, parentIndex=QtCore.QModelIndex()): # TODO: remove?
        childItem = StoreScalarTreeItem(name, value)
        return self.insertItem(childItem, position=position, parentIndex=parentIndex)
   
    
    def _itemValueForColumn(self, treeItem, column):
        """ Returns the value of the item given the column number.
            :rtype: string
        """
        try:
            if column == 0:
                return treeItem.nodeName
            elif column == 1:
                return str(treeItem.value)
            elif column == 2:
                return " x ".join(str(elem) for elem in treeItem.arrayShape)
            elif column == 3:
                return str(treeItem.arrayElemType)
            else:
                raise ValueError("Invalid column: {}".format(column))
        except AttributeError:
            # Not all items may have every attribute (e.g group items have only a name)
            if DEBUGGING:
                return "<Not found>"
            else:
                return ""
            

    def _setItemValueForColumn(self, treeItem, column, value):
        """ Sets the value in the item, of the item given the column number.
            It returns True for success, otherwise False.
        """
        if column == 1:
            treeItem.value = value
            return True
        else:
            if DEBUGGING:
                raise IndexError("Invalid column number: {}".format(column))
            return False


        
# Making a separate class instead of inheriting form BaseTreeModel/AbstractItemModel 
# as to keep the interface small.
   
class Repository(object):
    """ Keeps a list of stores (generally open files) and allows for adding and removing them.
    """
    
    def __init__(self):
        
        self._stores = []
        self._treeModel = RepositoryTreeModel() # TODO: move to selector
        
    
    @property
    def treeModel(self):
        return self._treeModel
        
    
    def appendStore(self, store):
        self._stores.append(store)
        storeRootItem = store.createItems()
        storeRootIndex = self.treeModel.insertItem(storeRootItem)
        return storeRootIndex
        
    
    def closeStore(self, store):
        assert False, "TODO: implement"

        
        