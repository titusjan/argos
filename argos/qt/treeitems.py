import logging

from argos.external import six
from argos.utils.cls import check_class, check_is_a_string

logger = logging.getLogger(__name__)

class BaseTreeItem(object):
    """ Base class for storing item data in a tree form. Each tree item represents a row
        in the BaseTreeModel (QAbstractItemModel).

        The tree items have no notion of which field is stored in which column. This is implemented
        in BaseTreeModel._itemValueForColumn
    """
    def __init__(self, nodeName):
        """ Constructor

            :param nodeName: short name describing this node. Is used to construct the nodePath.
                Currently we don't check for uniqueness in the children but this may change.
                The nodeName may not contain slashes (/).
        """
        check_class(nodeName, six.string_types, allow_none=False)
        assert nodeName, "nodeName may not be empty"
        assert '/' not in nodeName, "nodeName may not contain slashes"
        self._nodeName = str(nodeName)
        self._parentItem = None
        self._model = None
        self._childItems = [] # the fetched children
        self._nodePath = self._constructNodePath()

    def finalize(self):
        """ Can be used to cleanup resources. Should be called explicitly.
            Finalizes its children before closing itself
        """
        for child in self.childItems:
            child.finalize()

    def __str__(self):
        return "<{}: {}>".format(type(self).__name__, self.nodePath)

    def __repr__(self):
        return ("<{}: {!r}, children:[{}]>".
                format(type(self).__name__, self.nodePath,
                       ', '.join([repr(child) for child in self.childItems])))

    @property
    def model(self):
        """ Returns the ConfigTreeModel this item belongs to.
            If the model is None (not set), it will use and cache the parent's model.
            Therefore make sure that an ancestor node has a reference to the model! Typically by
            setting the model property of the invisible root item in the model constructor.
        """
        if self._model is None and self.parentItem is not None:
            self._model = self.parentItem.model
        return self._model

    @model.setter
    def model(self, value):
        """ Sets ConfigTreeModel this item belongs to.
        """
        self._model = value

#    @property
#    def modelIndex(self): # TODO: needed?
#        """ Returns the index in the ConfigTreeModel that refers to this item.
#        """
#        assert self._model, "Model not set for {}".format(self)
#        return self._model.indexFromItem(self)

#     Seems to be out of data and not used anymore
#     def emitDataChanged(self):
#         """ Causes the model associated with this item to emit a dataChanged() signal for this item.
#         """
#         assert self._model, "Model not set for {}".format(self)
#         return self._model.itemChanged(self)

    @property
    def decoration(self):
        """ An optional decoration (e.g. icon).
            The default implementation returns None (no decoration).
        """
        return None

    @property
    def font(self):
        """ Returns a font for displaying this item's text in the tree.
            The default implementation returns None (i.e. uses default font).
        """
        return None

    @property
    def backgroundBrush(self):
        """ Returns a brush for drawing the background role in the tree.
            The default implementation returns None (i.e. uses default brush).
        """
        return None

    @property
    def foregroundBrush(self):
        """ Returns a brush for drawing the foreground role in the tree.
            The default implementation returns None (i.e. uses default brush).
        """
        return None

    @property
    def sizeHint(self):
        """ Returns a size hint for displaying the items in the tree
            The default implementation returns None (i.e. no hint).
            Should return a QSize object or None
        """
        return None

    @property
    def nodeName(self):
        """ The node name. Is used to construct the nodePath"""
        return self._nodeName

    @nodeName.setter
    def nodeName(self, nodeName):
        """ The node name. Is used to construct the nodePath"""
        assert '/' not in nodeName, "nodeName may not contain slashes"
        self._nodeName = nodeName
        self._recursiveSetNodePath(self._constructNodePath())

    def _constructNodePath(self):
        """ Recursively prepends the parents nodeName to the path until the root node is reached."""
        if self.parentItem is None:
            return '' # invisible root node; is not included in the path
        else:
            return self.parentItem.nodePath + '/' + self.nodeName

    @property
    def nodePath(self):
        """ The sequence of nodeNames from the root to this node. Separated by slashes."""
        return self._nodePath

    def _recursiveSetNodePath(self, nodePath):
        """ Sets the nodePath property and updates it for all children.
        """
        self._nodePath = nodePath
        for childItem in self.childItems:
            childItem._recursiveSetNodePath(nodePath + '/' + childItem.nodeName)

    @property
    def parentItem(self):
        """ The parent item """
        return self._parentItem

    @parentItem.setter
    def parentItem(self, value):
        """ The parent item """
        self._parentItem = value
        self._recursiveSetNodePath(self._constructNodePath())

    @property
    def childItems(self):
        """ List of child items """
        #logger.debug("childItems {!r}".format(self))
        return self._childItems

    def hasChildren(self):
        """ Returns True if the item has children.

            If it has children the corresponding node in the tree can be expanded.
        """
        return len(self.childItems) > 0

    def nChildren(self): # TODO: numChildren
        """ Returns the number of children
        """
        return len(self.childItems)

    def child(self, row):
        """ Gets the child given its row number
        """
        return self.childItems[row]


    def childByNodeName(self, nodeName):
        """ Gets first (direct) child that has the nodeName.
        """
        assert '/' not in nodeName, "nodeName can not contain slashes"
        for child in self.childItems:
            if child.nodeName == nodeName:
                return child

        raise IndexError("No child item found having nodeName: {}".format(nodeName))


    def findByNodePath(self, nodePath):
        """ Recursively searches for the child having the nodePath. Starts at self.
        """
        def _auxGetByPath(parts, item):
            "Aux function that does the actual recursive search"
            #logger.debug("_auxGetByPath item={}, parts={}".format(item, parts))

            if len(parts) == 0:
                return item

            head, tail = parts[0], parts[1:]
            if head == '':
                # Two consecutive slashes. Just go one level deeper.
                return _auxGetByPath(tail, item)
            else:
                childItem = item.childByNodeName(head)
                return _auxGetByPath(tail, childItem)

        # The actual body of findByNodePath starts here

        check_is_a_string(nodePath)
        assert not nodePath.startswith('/'), "nodePath may not start with a slash"

        if not nodePath:
            raise IndexError("Item not found: {!r}".format(nodePath))

        return _auxGetByPath(nodePath.split('/'), self)


    def childNumber(self):
        """ Gets the index (nr) of this node in its parent's list of children.
        """
        # This is O(n) in time. # TODO: store row number in the items?
        if self.parentItem is not None:
            return self.parentItem.childItems.index(self)
        return 0


    def insertChild(self, childItem, position=None):
        """ Inserts a child item to the current item.
            The childItem must not yet have a parent (it will be set by this function).

            IMPORTANT: this does not let the model know that items have been added.
            Use BaseTreeModel.insertItem instead.

            param childItem: a BaseTreeItem that will be added
            param position: integer position before which the item will be added.
                If position is None (default) the item will be appended at the end.

            Returns childItem so that calls may be chained.
        """
        if position is None:
            position = self.nChildren()

        assert childItem.parentItem is None, "childItem already has a parent: {}".format(childItem)
        assert childItem._model is None, "childItem already has a model: {}".format(childItem)

        childItem.parentItem = self
        childItem.model = self.model
        self.childItems.insert(position, childItem)
        return childItem


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


    def logBranch(self, indent=0, level=logging.DEBUG):
        """ Logs the item and all descendants, one line per child
        """
        if 0:
            print(indent * "    " + str(self))
        else:
            logger.log(level, indent * "    " + str(self))
        for childItems in self.childItems:
            childItems.logBranch(indent + 1, level=level)



class AbstractLazyLoadTreeItem(BaseTreeItem):
    """ Abstract base class for a tree item that can do lazy loading of children.
        Descendants should override the _fetchAllChildren
    """
    def __init__(self, nodeName=''):
        """ Constructor
        """
        super(AbstractLazyLoadTreeItem, self).__init__(nodeName=nodeName)
        self._canFetchChildren = True # children not yet fetched (successfully or unsuccessfully)


    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children
        """
        return self._canFetchChildren or len(self.childItems) > 0


    def canFetchChildren(self):
        """ Returns True if children can be fetched, and False if they already have been fetched.
            Also returns False if they have been fetched and tried.
        """
        return self._canFetchChildren


    def fetchChildren(self):
        """ Fetches children.

            The actual work is done by _fetchAllChildren. Descendant classes should typically
            override that method instead of this one.
        """
        assert self._canFetchChildren, "canFetchChildren must be True"
        try:
            childItems = self._fetchAllChildren()
        finally:
            self._canFetchChildren = False # Set to True, even if tried and failed.

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
        try:
            super(AbstractLazyLoadTreeItem, self).removeAllChildren()
        finally:
            self._canFetchChildren = True
