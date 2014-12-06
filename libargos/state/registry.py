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

""" Classes to register plugins, data formats, etc
"""

import logging
from libargos.repo.treeitems import FileRtiMixin
from libargos.utils import prepend_point_to_extension


logger = logging.getLogger(__name__)



class RegisteredRti(object):
    """ Registered Repo Tree Item
    """
    def __init__(self, rtiClass, extensions=None):
        """ Constructor
        """
        if not issubclass(rtiClass, FileRtiMixin):
            raise TypeError("rtiClass must be a subtype of BaseRti".format(rtiClass))         
        self.rtiClass = rtiClass
        self.extensions = extensions if extensions is not None else []
        self.extensions = [prepend_point_to_extension(ext) for ext in self.extensions]
        
    def __repr__(self):
        return "<RegisteredRti: {}>".format(self.rtiClass)
        
        

class Registry(object):
    """ Class that can be used to register plug-ins, data formats, etc.
    """
    def __init__(self):
        """ Constructor
        """
        self._extensionToRti = {}
        self._registeredRtis = []
    
    @property
    def registeredRtis(self):
        return self._registeredRtis
    
    
    def registerRti(self, rtiClass, extensions=None):
        """ Register a RepoTreeItem class
        """
        regRti = RegisteredRti(rtiClass, extensions=extensions)
        logger.info("Registering {} for extensions: {}".format(regRti.rtiClass, regRti.extensions))
        for ext in regRti.extensions:
            if ext in self._extensionToRti:
                logger.warn("Overriding {} with {} for extension {!r}"
                            .format(self._extensionToRti[ext], regRti.rtiClass, ext))
            self._extensionToRti[ext] = regRti.rtiClass
                
        self._registeredRtis.append(regRti)

        
    def getRtiByExtension(self, extension):
        """ Returns the RepoTreeItem classes registered for that extension
        """
        return self._extensionToRti[extension]
        
