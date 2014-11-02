

from libargos.utils import check_class
from libargos.qt import QtGui, QtCore
from libargos.qt.editabletreemodel import TreeModel, BaseTreeItem



class ScalarTreeItem(BaseTreeItem):
    
    def __init__(self, name, value, parentItem=None):
        super(ScalarTreeItem, self).__init__(parentItem)
        self.name = name
        self.value = value 


    def columnValue(self, column):
        if column == 0:
            return self.name
        elif column == 1:
            return self.value
        else:
            raise ValueError("Invalid column: {}".format(column))
  
    

class RepositoryTreeModel(TreeModel):
    """ The main entry point of all the data
    
        Maintains a list of open files and  offers a QStandardDataModel for read-only access
    """
    
    def __init__(self, parent=None):
        """ Constructor
        """
        super(RepositoryTreeModel, self).__init__(headers=["name", "value"], parent=parent)
        

    def addScalar(self, name, value, position=None, parentIndex=QtCore.QModelIndex()):
        
        childItem = ScalarTreeItem(name, value)
        childIndex = self.insertChild(childItem, position, parentIndex)
        return childIndex
        
        
    
