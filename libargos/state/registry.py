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
from libargos.utils import prepend_point_to_extension, import_symbol, check_is_a_string


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
    
    
    def registerExtension(self, extension, rtiClass):
        """ Links an file name extension to a repository tree item. 
        """
        # TODO: type checking
        if extension in self._extensionToRti:
            logger.warn("Overriding {} with {} for extension {!r}"
                        .format(self._extensionToRti[extension], rtiClass, extension))
        self._extensionToRti[extension] = rtiClass
            
            
    def registerRti(self, rtiFullName, extensions=None):
        """ Register which Repo Tree Item should be used to open a particular file type.
                
            :param rtiFullName: full name of the repo tree item. 
                E.g.: 'libargos.plugins.rti.ncdf.NcdfFileRti'
                The rti should be a descendant of libargos.repo.treeitems.FileRtiMixin
            :param extensions: optional list of extensions that will be linked to this RTI
                a point will be prepended to the extensions if not already present.
        """
        check_is_a_string(rtiFullName)
        rtiClass = import_symbol(rtiFullName)
        
        regRti = RegisteredRti(rtiClass, extensions=extensions)
        self._registeredRtis.append(regRti)
        
        logger.info("Registering {} for extensions: {}".format(regRti.rtiClass, regRti.extensions))
        for ext in regRti.extensions:
            self.registerExtension(ext, regRti.rtiClass)

        
    def getRtiByExtension(self, extension):
        """ Returns the RepoTreeItem classes registered for that extension
        """
        return self._extensionToRti[extension]
        
