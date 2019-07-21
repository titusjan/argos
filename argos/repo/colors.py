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

""" Argos Color Library
"""
from __future__ import print_function

import logging
import os.path

from cmlib import CmLib, CmLibModel

from argos.utils.cls import SingletonMixin

logger = logging.getLogger(__name__)



class CmLibSingleton(CmLib, SingletonMixin):

    def __init__(self, **kwargs):
        super(CmLibSingleton, self).__init__(**kwargs)



class CmLibModelSingleton(CmLibModel, SingletonMixin):

    def __init__(self, **kwargs):
        super(CmLibModelSingleton, self).__init__(CmLibSingleton.instance(), **kwargs)

        # TODO: actual, relative path
        cmDataDir = os.path.abspath("/Users/kenter/prog/py/cmlib/cmlib/data")
        logger.info("Importing color map library from: {}".format(cmDataDir))

        # Don't import from Color Brewer since those are already included in MatPlotLib.
        # With sub-sampling the color maps similar maps can be achived as the Color Brewer maps.
        #self.cmLib.load_catalog(os.path.join(cmDataDir, 'ColorBrewer2'))
        self.cmLib.load_catalog(os.path.join(cmDataDir, 'CET'))
        self.cmLib.load_catalog(os.path.join(cmDataDir, 'MatPlotLib'))
        self.cmLib.load_catalog(os.path.join(cmDataDir, 'SciColMaps'))

        logger.debug("Number of color maps: {}".format(len(self.cmLib.color_maps)))

        # Set some random favorites to test the favorite checkbox


