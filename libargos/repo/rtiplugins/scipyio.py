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

""" Repository tree items that are read using import routines of Scipy
    See http://docs.scipy.org/doc/scipy-0.16.0/reference/io.html
"""
import logging, os
import scipy
import scipy.io

from libargos.qt import QtGui
from libargos.repo.memoryrtis import MappingRti
from libargos.repo.iconfactory import RtiIconFactory

logger = logging.getLogger(__name__)

ICON_COLOR_SCIPY = '#8800FF'


class IdlSaveFileRti(MappingRti):
    """ Can read data from an IDL 'save file'.

        Uses scipy.io.readsav to read the file. This reads all data at once when the file
        is open (in contrast to lazy loading each node separately). It therefor may take a while
        to read a large save-file. During this time the application is not responsive!
    """
    _iconKind = RtiIconFactory.FILE
    _iconColor = ICON_COLOR_SCIPY

    def __init__(self, nodeName='', fileName=''):
        """ Constructor. Initializes as an MappingRti with None as underlying dictionary.
        """
        super(IdlSaveFileRti, self).__init__(None, nodeName=nodeName, fileName=fileName)
        self._checkFileExists()

    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children 
        """
        return True

    def _openResources(self):
        """ Uses numpy.loadtxt to open the underlying file
        """
        self._dictionary = scipy.io.readsav(self._fileName)

    def _closeResources(self):
        """ Closes the underlying resources
        """
        self._dictionary = None
    
                        
