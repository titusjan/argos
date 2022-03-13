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

""" Repository tree items that are read using JSON
"""

import logging

from argos.external.json_with_comments import parse_json_with_comments_file
from argos.repo.baserti import BaseRti, lengthToSummary
from argos.repo.memoryrtis import _createFromObject
from argos.repo.iconfactory import RtiIconFactory, ICON_COLOR_UNDEF
from argos.utils.cls import is_a_sequence, is_a_mapping, is_an_array, type_name
from argos.utils.misc import pformat

logger = logging.getLogger(__name__)


def replace_lists_by_arrays(dct):
    """ Recursively walks a JSON dictionary and tries to replace"""


class JsonFileRti(BaseRti):
    """ Read JSON data with any comments filtered out.
        See https://github.com/sidneycadot/json_with_comments
    """
    _defaultIconGlyph = RtiIconFactory.FILE

    def __init__(self, nodeName='', fileName='', iconColor=ICON_COLOR_UNDEF):
        """ Constructor. Initializes as an MappingRti with None as underlying dictionary.
        """
        super(JsonFileRti, self).__init__(nodeName=nodeName, fileName=fileName,
                                         iconColor=iconColor)
        self._checkFileExists()
        self._data = None


    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children
        """
        return True


    def _openResources(self):
        """ Uses parse_json_with_comments_file to open the underlying file
        """
        self._data = parse_json_with_comments_file(self._fileName)
        logger.info("READ JSON: type = {}".format(type(self._data)))


    def _fetchAllChildren(self):
        """ Adds a child item for each item
        """
        childItems = []
        logger.debug("_fetchAllChildren of {!r} ({}):  {!r}"
                     .format(self, self.iconColor, self.fileName))

        if self.hasChildren():
            if is_a_sequence(self._data):
                for nr, elem in enumerate(self._data):
                    childItems.append(_createFromObject(
                        elem, nodeName="elem-{}".format(nr),
                        iconColor=self.iconColor, fileName=self.fileName))

            elif is_a_mapping(self._data):
                for key, value in self._data.items():
                    childItems.append(_createFromObject(
                        value, nodeName=str(key),
                        iconColor=self.iconColor, fileName=self.fileName))

            elif is_an_array(self._data):
                raise TypeError("Unexpected type in JSON: {}".format(type(self._data)))

            elif isinstance(self._data, bytearray):
                raise TypeError("Unexpected type in JSON: {}".format(type(self._data)))

            else:
                pass  # Data os a scalar so no add no children.

        return childItems


    def _closeResources(self):
        """ Closes the underlying resources
        """
        self._data = None


    def _containsScalar(self):
        """ Returns True if the JSON data consists of just a scalar

            Returns False if the file is closed.
        """
        return (self.isOpen and
                not is_a_sequence(self._data) and
                not is_a_mapping(self._data) and
                not is_an_array(self._data) and
                not isinstance(self._data, bytearray))


    @property
    def isSliceable(self):
        """ Returns True because the underlying data can be sliced.
            The scalar will be wrapped in an array with one element so it can be inspected.
        """
        return self._containsScalar()


    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
            The scalar will be wrapped in an array with one element so it can be inspected.
        """
        assert self._containsScalar(), "JSON element is only slicable when using a scalar"
        return self._data


    @property
    def arrayShape(self):
        """ Returns the shape of the wrapper array. Will always be an empty tuple()
        """
        assert self._containsScalar(), "JSON element is only slicable when using a scalar"
        return tuple()


    @property
    def dimensionality(self):
        """ String that describes if the RTI is an array, scalar, field, etc.
        """
        if not self.isOpen:
            return ""
        elif is_a_sequence(self._data):
            return "list"
        elif is_a_mapping(self._data):
            return ""
        elif is_an_array(self._data):
            return "array"
        elif isinstance(self._data, bytearray):
            return "array"
        else:
            return "scalar"

    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """

        if self._containsScalar():
            return type_name(self._data)
        else:
            return ""


    @property
    def summary(self):
        """ Returns a summary of the contents of the RTI.  E.g. 'array 20 x 30' elements.
        """
        if not self.isOpen:
            return ""
        elif is_a_sequence(self._data):
            return lengthToSummary(len(self._data))
        elif is_a_mapping(self._data):
            return ""  # emtpy to be in-line with other group RTIs
        elif is_an_array(self._data):
            raise NotImplementedError("Not (yet) implemented")
        elif isinstance(self._data, bytearray):
            raise NotImplementedError("Not (yet) implemented")
        else:
            return str(self._data)


    def quickLook(self, width: int):
        """ Returns a string representation fof the RTI to use in the Quik Look pane.

            We print all data, even if it is large, since it is already in memory, and it is
            assumed to be quick.
        """
        if not self.isOpen:
            return ""
        else:
            return pformat(self._data, width)
