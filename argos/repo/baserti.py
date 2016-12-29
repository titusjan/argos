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

""" Repository TreeItem (RTI) classes
    Tree items for use in the RepositoryTreeModel
"""
import logging
import os

from argos.external import six
from argos.info import DEBUGGING
from argos.qt.treeitems import AbstractLazyLoadTreeItem
from argos.repo.iconfactory import RtiIconFactory
from argos.utils.cls import check_class, is_a_sequence

logger = logging.getLogger(__name__)


class BaseRti(AbstractLazyLoadTreeItem):
    """ TreeItem for use in a RepositoryTreeModel. (RTI = Repository TreeItem)
        Base node from which to derive the other types of nodes.

        Serves as an interface but can also be instantiated for debugging purposes.
    """
    _defaultIconGlyph = None  # Can be overridden by defining a _iconGlyph attribute
    _defaultIconColor = None  # Can be overridden by defining a _iconColor attribute

    def __init__(self, nodeName, fileName=''):
        """ Constructor

            :param nodeName: name of this node (used to construct the node path).
            :param fileName: absolute path to the file where the data of this RTI originates.
        """
        super(BaseRti, self).__init__(nodeName=nodeName)

        self._isOpen = False
        self._exception = None # Any exception that may occur when opening this item.

        check_class(fileName, six.string_types, allow_none=True)
        if fileName:
            fileName = os.path.abspath(fileName)
        self._fileName = fileName


    @classmethod
    def createFromFileName(cls, fileName):
        """ Creates a BaseRti (or descendant), given a file name.
        """
        # See https://julien.danjou.info/blog/2013/guide-python-static-class-abstract-methods
        #logger.debug("Trying to create object of class: {!r}".format(cls))
        basename = os.path.basename(os.path.realpath(fileName)) # strips trailing slashes
        return cls(nodeName=basename, fileName=fileName)


    @property
    def fileName(self):
        """ Returns the name of the underlying the file.
        """
        return self._fileName


    def finalize(self):
        """ Can be used to cleanup resources. Should be called explicitly.
            Recursively calls the close method on all children and then on itself.
            In turn, close calls _closeRecources; descendants should override the latter.
        """
        for child in self.childItems:
            child.finalize()
        self.close()


    @property
    def isOpen(self):
        "Returns True if the underlying resources are opened"
        return self._isOpen


    def open(self):
        """ Opens underlying resources and sets isOpen flag.
            It calls _openResources. Descendants should usually override the latter
            function instead of this one.
        """
        self.clearException()
        try:
            if self._isOpen:
                logger.warn("Resources already open. Closing them first before opening.")
                self._closeResources()
                self._isOpen = False

            assert not self._isOpen, "Sanity check failed: _isOpen should be false"
            logger.debug("Opening {}".format(self))
            self._openResources()
            self._isOpen = True

            if self.model:
                self.model.sigItemChanged.emit(self)
            else:
                logger.warning("Model not set yet: {}".format(self))

        except Exception as ex:
            if DEBUGGING:
                raise
            logger.exception("Error during tree item open: {}".format(ex))
            self.setException(ex)


    def _openResources(self):
        """ Can be overridden to open the underlying resources.
            The default implementation does nothing.
            Is called by self.open
        """
        pass


    def close(self):
        """ Closes underlying resources and un-sets the isOpen flag.
            Any exception that occurs is caught and put in the exception property.
            This method calls _closeResources, which does the actual resource cleanup. Descendants
            should typically override the latter instead of this one.
        """
        self.clearException()
        try:
            if self._isOpen:
                logger.debug("Closing {}".format(self))
                self._closeResources()
                self._isOpen = False
            else:
                logger.debug("Resources already closed (ignored): {}".format(self))

            if self.model:
                self.model.sigItemChanged.emit(self)
            else:
                logger.warning("Model not set yet: {}".format(self))

        except Exception as ex:
            if DEBUGGING:
                raise
            logger.error("Error during tree item close: {}".format(ex))
            self.setException(ex)


    def _closeResources(self):
        """ Can be overridden to close the underlying resources.
            The default implementation does nothing.
            Is called by self.close
        """
        pass


    def _checkFileExists(self):
        """ Verifies that the underlying file exists and sets the _exception attribute if not
            Returns True if the file exists.
            If self._fileName is None, nothing is checked and True is returned.
        """
        if self._fileName and not os.path.exists(self._fileName):
            msg = "File not found: {}".format(self._fileName)
            logger.error(msg)
            self.setException(IOError(msg))
            return False
        else:
            return True

    @property
    def exception(self):
        """ The exception if an error has occurred during reading
        """
        return self._exception


    def setException(self, ex):
        """ Sets the exception attribute.
        """
        self._exception = ex


    def clearException(self):
        """ Forgets any stored exception to clear the possible error icon
        """
        self._exception = None


    def fetchChildren(self):
        """ Creates child items and returns them.
            Opens the tree item first if it's not yet open.
        """
        assert self._canFetchChildren, "canFetchChildren must be True"
        try:
            self.clearException()

            if not self.isOpen:
                self.open() # Will set self._exception in case of failure

            if not self.isOpen:
                logger.warn("Opening item failed during fetch (aborted)")
                return [] # no need to continue if opening failed.

            childItems = []
            try:
                childItems = self._fetchAllChildren()
                assert is_a_sequence(childItems), "ChildItems must be a sequence"

            except Exception as ex:
                # This can happen, for example, when a NCDF/HDF5 file contains data types that
                # are not supported by the Python library that is used to read them.
                if DEBUGGING:
                    raise
                logger.error("Unable fetch tree item children: {}".format(ex))
                self.setException(ex)

            return childItems
        finally:
            self._canFetchChildren = False


    def _fetchAllChildren(self):
        """ The function that actually fetches the children. Default returns no children.
        """
        return []


    @property
    def iconColor(self):
        """ Returns the color of the icon (.e.g. '#FF0000' for red).
            If self contains a _iconColor attribute, this is returned.
            Otherwise the _defaultIconColor of the class is returned.
            :rtype: string
        """
        if hasattr(self, "_iconColor"): # TODO: probably better override this in descendants.
            return getattr(self, "_iconColor")
        else:
            return self._defaultIconColor


    @property
    def iconGlyph(self):
        """ Returns the kind of the icon (e.g. RtiIconFactory.FILE, RtiIconFactory.ARRAY, etc).
            The base implementation returns the default glyph of the class.
            :rtype: string
        """
        if hasattr(self, "_iconGlyph"):
            return getattr(self, "_iconGlyph")
        else:
            return self._defaultIconGlyph


    @property
    def decoration(self):
        """ The displayed icon.

            Shows open icon when node was visited (children are fetched). This allows users
            for instance to collapse a directory node but still see that it was visited, which
            may be useful if there is a huge list of directories.
        """
        rtiIconFactory = RtiIconFactory.singleton()

        if self._exception:
            return rtiIconFactory.getIcon(rtiIconFactory.ERROR, isOpen=False,
                                          color=rtiIconFactory.COLOR_ERROR)
        else:
            return rtiIconFactory.getIcon(self.iconGlyph, isOpen=not self.canFetchChildren(),
                                          color=self.iconColor)

    @property
    def isSliceable(self):
        """ Returns True if the underlying data can be sliced.
            An inspector should always check this before using an index/slice on an RTI.

            The base implementation returns False. Descendants should override this if they contain
            an array that can be sliced.
        """
        return False


    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).

            The base function is abstract. Descendants should override this if they contain
            an array that can be sliced (i.e. self.isSliceable is True). It should then
            call __getitem__(index) on the underlying array data.
        """
        raise NotImplemented("Override for slicable arrays")


    @property
    def nDims(self): # TODO: rename to numDims?
        """ The number of dimensions of the underlying array
            The base implementation returns len(self.arrayShape). Descendants may override this to
            provide a more efficient implementation
        """
        return len(self.arrayShape)


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
            The base function is abstract. Descendants should override this if they contain
            an array that can be sliced (i.e. self.isSliceable is True).
        """
        raise NotImplemented("Override for slicable arrays")


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        return ""


    # TODO: setter?
    @property
    def attributes(self):
        """ The attribute dictionary.
            The attributes generally contain meta data about the item.
        """
        return {}


    @property
    def dimensionNames(self):
        """ Returns a list with the name of each of the RTI's dimensions.
            The default implementation returns ['Dim0', 'Dim1', ...] by default. Descendants can
            override this.
        """
        return ['Dim{}'.format(dimNr) for dimNr in range(self.nDims)] # TODO: cache?


    @property
    def dimensionGroupPaths(self):
        """ Returns a list with, for every dimension, the path of the group that contains it.
            The default implementation returns an empty string for each dimension. Descendants
            can override this.
        """
        return ['' for _dimNr in range(self.nDims)] # TODO: cache?


    @property
    def unit(self):
        """ Returns the unit of the RTI. The base implementation returns ''.
        """
        return ""


    @property
    def missingDataValue(self):
        """ Returns the value to indicate missing data.

            The base implementation returns None, indicating that there is no missing data
            specified.
        """
        return None


#    @property
#    def dimensionInfo(self):
#        """ Returns a list with a DimensionInfo objects for each of the RTI's dimensions.
#            The default Returns ['Dim0', 'Dim1', ...] by default. Descendants can override this.
#        """
#        return ['Dim{}'.format(dimNr) for dimNr in range(self.nDims)]
#
#
#
#class DimensionInfo(object):
#    """ Stores attributes (name, size, etc) of a Dimension
#    """
#    def __init__(self, name, size):
#        """ Constructor
#        """
#        self._name = name
#        self._size = size
#
#    @property
#    def name(self):
#        """ The dimension name
#        """
#        return self._name
#
#    @property
#    def size(self):
#        """ The dimension size
#        """
#        return self._size
#
#
