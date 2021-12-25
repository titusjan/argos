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
import pathlib
import importlib
import importlib.resources
from os import listdir

from cmlib import CmLib, CmLibModel, DATA_DIR

from argos.utils.cls import SingletonMixin

logger = logging.getLogger(__name__)

# The color maps that are favorites then the program is started for the first time or reset.
DEF_FAV_COLOR_MAPS = [
    'SciColMaps/Oleron', 'SciColMaps/Nuuk', 'SciColMaps/Acton', 'CET/CET-CBL2', 'MatPlotLib/Gray',
    'CET/CET-C2', 'CET/CET-R2', 'MatPlotLib/BrBG', 'MatPlotLib/Tab20', 'MatPlotLib/Magma',
    'MatPlotLib/Tab10', 'MatPlotLib/Cubehelix', 'MatPlotLib/Viridis', 'MatPlotLib/Coolwarm']

DEFAULT_COLOR_MAP = "MatPlotLib/Magma"
assert DEFAULT_COLOR_MAP in DEF_FAV_COLOR_MAPS, "Default color map not in default favorites."


class CmLibSingleton(CmLib, SingletonMixin):
    def __init__(self, **kwargs):
        super(CmLibSingleton, self).__init__(**kwargs)
        logger.debug("CmLib singleton: {}".format(self))
        #cmDataDir = DATA_DIR
        # Don't import from Color Brewer since those are already included in MatPlotLib.
        # With sub-sampling the color maps similar maps can be achieved as the Color Brewer maps
        excludeList = ['ColorBrewer2', "readme.txt", "__init__.py", "__pycache__"]
        for path in importlib.resources.contents(f"cmlib.data"):
            if any(item in path for item in excludeList):
                logger.debug("Not importing catalogue from exlude list: {}".format(excludeList))
                continue
            self.load_catalog(pathlib.Path(path))
        logger.debug("Number of color maps: {}".format(len(self.color_maps)))


class CmLibModelSingleton(CmLibModel, SingletonMixin):

    def __init__(self, **kwargs):
        super(CmLibModelSingleton, self).__init__(CmLibSingleton.instance(), **kwargs)
