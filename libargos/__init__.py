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

""" Functionality for Argos

    This is the top level module and should not be imported by sub modules.
    The only way is up in that respect.
"""
import logging
from .info import VERSION as __version__
from .application import getArgosApplication

logger = logging.getLogger(__name__)

def browse(fileNames = None, resetProfile=False): 
    """ Opens a main window and executes the application
    """
    #if DEBUGGING: # TODO temporary
    #    _gcMon = createGcMonitor()
    argosApp = getArgosApplication()
    argosApp.readViewSettings(reset=resetProfile)
    if argosApp.nMainWindows == 0:
        logger.warn("No open windows in profile. Creating one.")
        argosApp.createMainWindow(fileNames = fileNames) # TODO: filenames should be part of the app
    exitCode = argosApp.execute()
    logger.debug("Event loop finished.")
    return exitCode

