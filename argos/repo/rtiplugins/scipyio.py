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
from __future__ import absolute_import

import logging, os
import scipy
import scipy.io
import scipy.io.wavfile

from argos.repo.memoryrtis import ArrayRti, SliceRti, MappingRti
from argos.repo.iconfactory import RtiIconFactory, ICON_COLOR_UNDEF

logger = logging.getLogger(__name__)


class MatlabFileRti(MappingRti):
    """ Read data from a MATLAB file using the scipy.io.loadmat function.

        Note: v4 (Level 1.0), v6 and v7 to 7.2 matfiles are supported.

        From version 7.3 onward matfiles are stored in HDF-5 format. You can read them with the
        Argos hDF-5 plugin (which uses on h5py)
    """
    _defaultIconGlyph = RtiIconFactory.FILE

    def __init__(self, nodeName='', fileName='', iconColor=ICON_COLOR_UNDEF):
        """ Constructor. Initializes as an MappingRti with None as underlying dictionary.
        """
        super(MatlabFileRti, self).__init__(None, nodeName=nodeName, fileName=fileName,
                                            iconColor=iconColor)
        self._checkFileExists()


    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children
        """
        return True


    def _openResources(self):
        """ Uses numpy.loadtxt to open the underlying file
        """
        self._dictionary = scipy.io.loadmat(self._fileName)


    def _closeResources(self):
        """ Closes the underlying resources
        """
        self._dictionary = None



class IdlSaveFileRti(MappingRti):
    """ ReadS data from an IDL 'save file'.

        Uses scipy.io.readsav to read the file. This reads all data at once when the file
        is open (in contrast to lazy loading each node separately). Therefore, it may take a while
        to read a large save-file. During this time the application is not responsive!
    """
    _defaultIconGlyph = RtiIconFactory.FILE

    def __init__(self, nodeName='', fileName='', iconColor=ICON_COLOR_UNDEF):
        """ Constructor. Initializes as an MappingRti with None as underlying dictionary.
        """
        super(IdlSaveFileRti, self).__init__(None, nodeName=nodeName, fileName=fileName,
                                             iconColor=iconColor)
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



class WavFileRti(ArrayRti):
    """ Read data from a WAV file using the scipy.io.wavfile.read function

        First tries to read with memory mapping, if that fails it tries to read the file without
        memory mapping.
    """
    _defaultIconGlyph = RtiIconFactory.FILE

    def __init__(self, nodeName='', fileName='', iconColor=ICON_COLOR_UNDEF):
        """ Constructor. Initializes as an ArrayRTI with None as underlying array.
        """
        super(WavFileRti, self).__init__(None, nodeName=nodeName, fileName=fileName,
                                         iconColor=iconColor)
        self._checkFileExists()


    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children
        """
        return True


    def _openResources(self):
        """ Uses numpy.loadtxt to open the underlying file.
        """
        try:
            rate, data = scipy.io.wavfile.read(self._fileName, mmap=True)
        except Exception as ex:
            logger.warning(ex)
            logger.warning("Unable to read wav with memmory mapping. Trying without now.")
            rate, data = scipy.io.wavfile.read(self._fileName, mmap=False)

        self._array = data
        self.attributes['rate'] = rate


    def _closeResources(self):
        """ Closes the underlying resources
        """
        self._array = None
        self.attributes.clear()


    def _fetchAllChildren(self):
        """ Adds an ArrayRti per column as children so that they can be inspected easily
        """
        childItems = []
        if self._array.ndim == 2:
            _nRows, nCols = self._array.shape if self._array is not None else (0, 0)
            for col in range(nCols):
                colItem = SliceRti(self._array[:, col], nodeName="channel-{}".format(col),
                                   fileName=self.fileName, iconColor=self.iconColor,
                                   attributes=self.attributes)
                childItems.append(colItem)
        return childItems

