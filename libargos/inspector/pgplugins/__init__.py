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

""" Plugins that use the PyQtGraph plot library.
"""
import pyqtgraph as pg
import logging

logger = logging.getLogger(__name__)

def setPgConfigOptions(**kwargs):
    """ Sets the PyQtGraph config options and emits a log message
    """
    for key, value in kwargs.items():
        logger.debug("Setting PyQtGraph config option: {} = {}".format(key, value))
    
    pg.setConfigOptions(**kwargs) 


# Sets some config options
setPgConfigOptions(antialias=True, exitCleanup=False, crashWarning=True) 


