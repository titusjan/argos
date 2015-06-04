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
from libargos.utils.cls import check_is_a_string, check_class
from libargos.utils.misc import prepend_point_to_extension
from libargos.qt.registry import RegisteredClassItem, ClassRegistry

logger = logging.getLogger(__name__)


class RegisteredRti(RegisteredClassItem):
    """ Class to keep track of a registered Repo Tree Item.
    """
    def __init__(self, identifier, fullClassName, extensions):
        """ Constructor. See the RegisteredClassItem class doc string for the parameter help.
        """
        super(RegisteredRti, self).__init__(identifier, fullClassName)
        self._extensions = [prepend_point_to_extension(ext) for ext in extensions]
        

    @property
    def extensions(self):
        """ Extensions that will automatically open as this RTI.
        """
        return self._extensions
    
    
    def getFileDialogFilter(self):
        """ Returns a filters that can be used to construct file dialogs filters, 
            for example: 'Txt (*.txt;*.text)'    
        """
        extStr = ';'.join(['*' + ext for ext in self.extensions])
        return '{} ({})'.format(self.rtiShortName, extStr)
    
        
    def asDict(self):
        """ Returns a dictionary for serialization.
        """
        return {'identifier': self.identifier, 
                'fullClassName': self.fullClassName, 
                'extensions': self.extensions}
        

class RtiRegistry(ClassRegistry):
    """ Class that can be used to register repository tree items (RTIs).
    
        Maintains a name to RtiClass mapping and an extension to RtiClass mapping.
        The extension in the extensionToRti assure that a unique RTI is used as default mapping, 
        the extensions in the RegisteredRti class do not have to be unique and are used in the
        filter in the getFileDialogFilter function. 
    """
    def __init__(self, settingsGroupName=None):
        """ Constructor
        """
        super(RtiRegistry, self).__init__(settingsGroupName=settingsGroupName)
        self._itemClass = RegisteredRti
        self._extensionMap = {}
        
        
    def clear(self):
        """ Empties the registry
        """
        super(RtiRegistry, self).clear()
        self._extensionMap = {}
    
    
    def _registerExtension(self, extension, registeredRti):
        """ Links an file name extension to a repository tree item. 
        """
        check_is_a_string(extension)
        check_class(registeredRti, RegisteredRti)
         
        logger.debug("_____Registering {} for extension {!r}".format(registeredRti, extension))        
        
        # TODO: type checking
        if extension in self._extensionMap:
            logger.warn("Overriding {} with {} for extension {!r}"
                        .format(self._extensionMap[extension], registeredRti, extension))
        self._extensionMap[extension] = registeredRti
    
            
    def registerItem(self, item):
        """ Adds a RegisteredClassItem object to the registry.
        """
        super(RtiRegistry, self).registerItem(item)
                
        for ext in item.extensions:
            self._registerExtension(ext, item) 
            
            
    def registerRti(self, identifier, fullClassName, extensions=None):
        """ Class that maintains the collection of registered inspector classes.
            Maintains a lit of file extensions that open the RTI by default. 
        """
        extensions = extensions if extensions is not None else []
        extensions = [prepend_point_to_extension(ext) for ext in extensions]

        regRti = RegisteredRti(identifier, fullClassName, extensions)
        self.registerItem(regRti)


        
    def getRtiByExtension(self, extension):
        """ Returns the RepoTreeItem classes registered for that extension
        """
        registeredRti = self._extensionMap[extension]
        rti = registeredRti.getClass(tryImport=True)
        return rti
    
    
    def getFileDialogFilter(self):
        """ Returns a filter that can be used in open file dialogs, 
            for example: 'All files (*);;Txt (*.txt;*.text);;netCDF(*.nc;*.nc4)'    
        """
        filters = ['All files (*)']
        for regRti in self._registeredRtis:
            filters.append(regRti.getFileDialogFilter())
        return ';;'.join(filters)
    

    def getDefaultItems(self):
        """ Returns a list with the default plugins in the repo tree item registry.
        """
        return [
            RegisteredRti('NCDF file', 
                          'libargos.repo.rtiplugins.ncdf.NcdfFileRti', 
                          extensions=['nc', 'nc3', 'nc4']),
                   
            RegisteredRti('NumPy text file', 
                          'libargos.repo.rtiplugins.nptextfile.NumpyTextFileRti', 
                          extensions=['txt', 'text'])]
        

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


            