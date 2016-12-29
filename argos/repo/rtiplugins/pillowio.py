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

""" Uses the Python Imaging Library (Pillow) to open an image
"""
import logging
import numpy as np

from PIL import Image

from argos.info import DEBUGGING
from argos.repo.iconfactory import RtiIconFactory
from argos.repo.memoryrtis import ArrayRti, SliceRti

logger = logging.getLogger(__name__)

ICON_COLOR_PILLOW = '#880088'


class PillowBandRti(SliceRti):
    """ Image band repo tree item. Will typically be a child of a PillowFileRti

        No dedicated constructor defined (reuses the ArrayRti constructor)
    """

    @property
    def dimensionNames(self):
        """ Returns ['Y', 'X'].
            The underlying array is expected to be 2-dimensional. If this is not the case we fall
            back on the default dimension names ['Dim-0', 'Dim-1', ...]
        """
        if self._array is None:
            return []

        if self._array.ndim != 2:
            # Defensive programming: fall back on default names
            msg = "Expected 2D image. Got: {}".format(self._array.ndim)
            if DEBUGGING:
                raise ValueError(msg)
            logger.warn(msg)
            return super(PillowBandRti, self).dimensionNames
        else:
            return ['Y', 'X']



class PillowFileRti(ArrayRti):
    """ Opens an image file with the Python Imaging Library (Pillow)

        See https://python-pillow.org/
    """
    _defaultIconGlyph = RtiIconFactory.FILE
    _defaultIconColor = ICON_COLOR_PILLOW

    def __init__(self, nodeName='', fileName=''):
        """ Constructor. Initializes as an ArrayRTI with None as underlying array.
        """
        super(PillowFileRti, self).__init__(None, nodeName=nodeName, fileName=fileName,
                                            iconColor=self._defaultIconColor)
        self._checkFileExists()
        self._bands = [] # image band names


    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children
        """
        return True


    def _openResources(self):
        """ Uses  open the underlying file
        """
        with Image.open(self._fileName) as image:
            self._array = np.asarray(image)
            self._bands = image.getbands()

            # Fill attributes. For now assume that the info item are not overridden by
            # the Image items.
            self._attributes = dict(image.info)
            self._attributes['Format'] = image.format
            self._attributes['Mode'] = image.mode
            self._attributes['Size'] = image.size
            self._attributes['Width'] = image.width
            self._attributes['Height'] = image.height


    def _closeResources(self):
        """ Closes the underlying resources
        """
        self._array = None
        self._bands = []
        self._attributes = {}


    def _fetchAllChildren(self):
        """ Adds the bands as separate fields so they can be inspected easily.
        """
        bands = self._bands
        if len(bands) != self._array.shape[-1]:
            logger.warn("No bands added, bands != last_dim_lenght ({} !: {})"
                        .format(len(bands), self._array.shape[-1]))
            return []

        childItems = []
        for bandNr, band in enumerate(bands):
            bandItem = PillowBandRti(self._array[..., bandNr],
                                     nodeName=band, fileName=self.fileName,
                                     iconColor=self.iconColor, attributes=self._attributes)
            childItems.append(bandItem)
        return childItems


    @property
    def attributes(self):
        """ The attribute dictionary. Con
        """
        return self._attributes


    @property
    def dimensionNames(self):
        """ Returns ['Y', 'X', 'Band'].
            The underlying array is expected to be 3-dimensional. If this is not the case we fall
            back on the default dimension names ['Dim-0', 'Dim-1', ...]
        """
        if self._array is None:
            return []

        if self._array.ndim == 2:
            return ['Y', 'X']
        elif self._array.ndim == 3:
            return ['Y', 'X', 'Band']
        else:
            # Defensive programming: fall back on default names
            msg = "Expected 3D image. Got: {}".format(self._array.ndim)
            if DEBUGGING:
                raise ValueError(msg)
            logger.warn(msg)
            return super(PillowFileRti, self).dimensionNames

