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

import json
import logging
import os

from argos.external.json_with_comments import parse_json_with_comments_file
from argos.repo.memoryrtis import ArrayRti, SliceRti, MappingRti
from argos.repo.iconfactory import RtiIconFactory, ICON_COLOR_UNDEF

logger = logging.getLogger(__name__)


class JsonFileRti(MappingRti):
    """ Read JSON data with any comments filtered out.
        See https://github.com/sidneycadot/json_with_comments
    """
    _defaultIconGlyph = RtiIconFactory.FILE

    def __init__(self, nodeName='', fileName='', iconColor=ICON_COLOR_UNDEF):
        """ Constructor. Initializes as an MappingRti with None as underlying dictionary.
        """
        super(JsonFileRti, self).__init__(None, nodeName=nodeName, fileName=fileName,
                                         iconColor=iconColor)
        self._checkFileExists()


    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children
        """
        return True


    def _openResources(self):
        """ Uses numpy.loadtxt to open the underlying file
        """
        self._dictionary = parse_json_with_comments_file(self._fileName)


    def _closeResources(self):
        """ Closes the underlying resources
        """
        self._dictionary = None

