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
from .info import DEBUGGING, DEFAULT_PROFILE
from .application import ArgosApplication

logger = logging.getLogger(__name__)

def browse(fileNames = None, 
           profile=DEFAULT_PROFILE, 
           resetProfile=False, 
           resetAllProfiles=False): 
    """ Opens a main window and executes the application
    """
    #if DEBUGGING: # TODO temporary
    #    _gcMon = createGcMonitor()
    argosApp = ArgosApplication()
    if DEBUGGING:
        __addTestData(argosApp)
    argosApp.loadFiles(fileNames)
    if resetProfile:
        argosApp.deleteProfile(profile)
    if resetAllProfiles:
        argosApp.deleteAllProfiles()
    argosApp.loadProfile(profile=profile)
    return argosApp.execute()


def __addTestData(argosApp):
    """ Temporary function to add test data
    """
    import numpy as np
    from libargos.repo.memoryrtis import MappingRti
    myDict = {}
    myDict['name'] = 'Pac Man'
    myDict['age'] = 34
    myDict['ghosts'] = ['Inky', 'Blinky', 'Pinky', 'Clyde']
    myDict['array'] = np.arange(24).reshape(3, 8)
    myDict['subDict'] = {'mean': np.ones(111), 'stddev': np.zeros(111, dtype=np.uint16)}
    
    mappingRti = MappingRti(myDict, nodeName="myDict", fileName='')
    argosApp.repo.insertItem(mappingRti)


