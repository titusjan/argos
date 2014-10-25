

from libargos.utils import check_class
from libargos.qt import QtGui, QtCore
from libargos.qt.editabletreemodel import TreeModel, TreeItem

#
#def addDictionary(standardItem, dictionary):
#    
#    for key, value in dictionary.items():
#        
#        standardItem

#
#def insertChildItem(childItem, parentIndex, beforeRow=None):
#    
#    check_class(parentIndex, QtCore.QAbstractItemModel)
#    check_class(childItem, TreeItem)
#    
#    if beforeRow is None:
#        beforeRow = 0 # TODO: last
#
#    # Add new row to the model
#    model = parentIndex.model()
#    success = model.insertRow(beforeRow, parentIndex)
#    if not success:
#        AssertionError("Unable to insert new row in model {!r} at position {}"
#                       .format(model, beforeRow))
#
#    # Add childItem to the underlying TreeItem node
#    parentItem = parentIndex.internalPointer()
#    assert parentItem, "Unable underlying item of {!r} is {!r}".format(parentIndex, parentItem)
#    parentItem.insertChilde



    

class RepositoryTreeModel(TreeModel):
    """ The main entry point ot all the data
    
        Maintains a list of open files and  offers a QStandardDataModel for read-only access
    """
    
    def __init__(self, parent=None):
        """ Constructor
        """
        super(RepositoryTreeModel, self).__init__(headers=["name", "value"], parent=parent)
        
    
    def addScalar(self, name, value, position=None, parentIndex=QtCore.QModelIndex()):
        
        childItem = TreeItem(data=(name, value))
        self.insertChild(childItem, position, parentIndex)
        return childItem
        
        
    
