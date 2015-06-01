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

""" Defines a global RTI registry to register repository tree item plugins.
"""

import logging
from libargos.utils.cls import import_symbol, check_is_a_string
from libargos.utils.misc import prepend_point_to_extension


logger = logging.getLogger(__name__)



class _RegisteredRti(object):
    """ Class to keep track of a registered Repo Tree Item.
        For internal use only.
    """
    def __init__(self, rtiFullName, rtiClass, extensions):
        self.rtiFullName = rtiFullName
        self.rtiClass = rtiClass
        self.extensions = extensions
        # TODO: register shortcuts?
        
        
    def __repr__(self):
        return "<_RegisteredRti: {}>".format(self.rtiShortName)
        
        
    @property
    def rtiShortName(self):
        """ Short name for use in file dialogs, menus, etc.
        """
        return self.rtiFullName.rsplit('.', 1)[1]
    

    def getFileDialogFilter(self):
        """ Returns a filters that can be used to construct file dialogs filters, 
            for example: 'Txt (*.txt;*.text)'    
        """
        extStr = ';'.join(['*' + ext for ext in self.extensions])
        return '{} ({})'.format(self.rtiShortName, extStr)
    

class RtiRegistry(object):
    """ Class that can be used to register repository tree items (RTIs).
    
        Maintains a name to RtiClass mapping and an extension to RtiClass mapping. 
    """
    def __init__(self):
        """ Constructor
        """
        self._extensionToRti = {}
        self._registeredRtis = []
    
    @property
    def registeredRtis(self):
        return self._registeredRtis
    
    
    def _registerExtension(self, extension, rtiClass):
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
                E.g.: 'libargos.repo.rtiplugins.ncdf.NcdfFileRti'
                The rti should be a descendant of BaseRti
            :param extensions: optional list of extensions that will be linked to this RTI
                a point will be prepended to the extensions if not already present.
        """
        extensions = extensions if extensions is not None else []
        extensions = [prepend_point_to_extension(ext) for ext in extensions]
        logger.info("Registering {} for extensions: {}".format(rtiFullName, extensions))
        
        check_is_a_string(rtiFullName)
        rtiClass = import_symbol(rtiFullName) # TODO: check class? 
        
        regRti = _RegisteredRti(rtiFullName, rtiClass, extensions)
        self._registeredRtis.append(regRti)
        
        for ext in regRti.extensions:
            self._registerExtension(ext, regRti.rtiClass)

        
    def getRtiByExtension(self, extension):
        """ Returns the RepoTreeItem classes registered for that extension
        """
        return self._extensionToRti[extension]
    
    
    def getFileDialogFilter(self):
        """ Returns a filter that can be used in open file dialogs, 
            for example: 'All files (*);;Txt (*.txt;*.text);;netCDF(*.nc;*.nc4)'    
        """
        filters = ['All files (*)']
        for regRti in self._registeredRtis:
            filters.append(regRti.getFileDialogFilter())
        return ';;'.join(filters)
    

# The RTI registry is implemented as a singleton. This is necessary because
# in DirectoryRti._fetchAllChildren we need access to the registry. 
# TODO: think of an elegant way to access the ArgosApplication.registry from there.    
def createGlobalRegistryFunction():
    """ Closure to create the RtiRegistry singleton
    """
    globReg = RtiRegistry()
    
    def accessGlobalRegistry():
        return globReg
    
    return accessGlobalRegistry

# This is actually a function definition, not a constant
#pylint: disable=C0103

globalRtiRegistry = createGlobalRegistryFunction()
globalRtiRegistry.__doc__ = "Function that returns the RtiRegistry singleton common to all windows"


            