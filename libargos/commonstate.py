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

""" State that is shared between all windows.
"""
import logging

from libargos.utils import type_name
from libargos.selector.repository import Repository
from libargos.repo.registry import Registry

logger = logging.getLogger(__name__)

class StateSingleton(object):
    """ Singleton object that stores the shared state between all windows
    """
    def __init__(self):
        """ Constructor """
        self._registry = Registry()
        self._repository = Repository()
        
        
    def __repr__(self):
        return "<{}>".format(type_name(self))
    
    @property        
    def registry(self):
        """ Returns the data repository """
        return self._registry

    @property        
    def repository(self):
        """ Returns the data repository """
        return self._repository
    

def createCommonStateFunction():
    """ Closure to create the StateSingleton
    """
    cstate = StateSingleton()
    
    def accessCommonState():
        return cstate
    
    return accessCommonState

getCommonState = createCommonStateFunction()
getCommonState.__doc__ = "Function that returns the StateSingleton common to all windows"

