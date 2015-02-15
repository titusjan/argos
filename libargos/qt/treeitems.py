
import logging


logger = logging.getLogger(__name__)

class BaseTreeItem(object):
    """ Base class for storing item data in a tree form. Each tree item represents a row
        in the BaseTreeModel (QAbstractItemModel). 
        
        The tree items have no notion of which field is stored in which column. This is implemented
        in BaseTreeModel._itemValueForColumn
    """
    def __init__(self):
        self._parentItem = None
        self._childItems = [] # the fetched children

    def finalize(self):
        """ Can be used to cleanup resources. Should be called explicitly.
            Finalizes its children before closing itself
        """
        for child in self.childItems:
            child.finalize()
        
    def __repr__(self):
        return "<{}>".format(type(self).__name__)
    
    @property
    def parentItem(self):
        """ The parent item """
        return self._parentItem
    
    @parentItem.setter
    def parentItem(self, value):
        """ The parent item """
        self._parentItem = value
    
    @property
    def childItems(self):
        """ List of child items """
        #logger.debug("childItems {!r}".format(self))
        return self._childItems

    def hasChildren(self):
        """ Returns True if the item has children 
        """
        return len(self.childItems) > 0

    def child(self, row):
        return self.childItems[row]

    def nChildren(self):
        return len(self.childItems)

    def childNumber(self):
        """ Gets the index (nr) of this node in its parent's list of children
        """
        if self.parentItem != None:
            return self.parentItem.childItems.index(self)
        return 0


    def insertChild(self, childItem, position=None): 
        
        if position is None:
            position = self.nChildren()
            
        assert 0 <= position <= len(self.childItems), \
            "position should be 0 < {} <= {}".format(position, len(self.childItems))
            
        assert childItem.parentItem is None, "childItem already has a parent: {}".format(childItem)
            
        childItem.parentItem = self    
        self.childItems.insert(position, childItem)


    def removeChild(self, position):
        """ Removes the child at the position 'position'
            Calls the child item finalize to close its resources before removing it.
        """
        assert 0 <= position <= len(self.childItems), \
            "position should be 0 < {} <= {}".format(position, len(self.childItems))

        self.childItems[position].finalize()
        self.childItems.pop(position)


    def removeAllChildren(self):
        """ Removes the all children of this node.
            Calls the child items finalize to close their resources before removing them.
        """
        for childItem in self.childItems:
            childItem.finalize()
        self._childItems = []


    
class AbstractLazyLoadTreeItem(BaseTreeItem):
    """ Abstract base class for a tree item that can do lazy loading of children.
        Descendants should override the _fetchAllChildren
    """
    def __init__(self):
        """ Constructor
        """
        super(AbstractLazyLoadTreeItem, self).__init__()
        self._childrenFetched = False
        
    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children 
        """
        return True
        #return not self._childrenFetched or len(self.childItems) > 0 TODO: use this? 
        
    def canFetchChildren(self):
        return not self._childrenFetched
        
    def fetchChildren(self):
        assert not self._childrenFetched, "canFetchChildren must be True"
        childItems = self._fetchAllChildren()
        self._childrenFetched = True
        return childItems
    
    def _fetchAllChildren(self):
        """ The function that actually fetches the children.
        
            The result must be a list of RepoTreeItems. Their parents must be None, 
            as that attribute will be set by BaseTreeitem.insertItem()
         
            :rtype: list of BaseRti objects
        """ 
        raise NotImplementedError
    
    def removeAllChildren(self):
        """ Removes all children """
        super(AbstractLazyLoadTreeItem, self).removeAllChildren()
        self._childrenFetched = False
     