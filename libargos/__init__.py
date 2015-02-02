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

from .info import VERSION as __version__
from .application import getArgosApplication

def browse(fileNames = None, **kwargs):
    """ Opens and executes a main window
    """
    #if DEBUGGING: # TODO temporary
    #    _gcMon = createGcMonitor()
    argosApp = getArgosApplication()
    argosApp.createMainWindow(fileNames = fileNames, **kwargs)
    exitCode = argosApp.execute()
    return exitCode

