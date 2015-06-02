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

""" Defines a global Inspector registry to register plugins.
"""

import logging, inspect, os
from libargos.info import DEBUGGING
from libargos.utils.cls import import_symbol, check_is_a_string, type_name, check_class

logger = logging.getLogger(__name__)


class RegisteredClass(object):
    """ Represents an class that is registered in the registry. Each class has an identifier that
        must be unique and a class name with the location of the class.
        The underlying class is not imported by default; use tryImportClass or getClass() for this.
    """
    def __init__(self, identifier, fullClassName):
        """ Constructor.
        
            :param identifier: identifier comprising of library and name, separated by a slash.
                Can contain spaces. E.g.: 'library name/My Widget'
                Must be unique when spaces are removed and converted to lower case. 
            :param fullClassName: full name of the underlying class. 
                E.g.: 'libargos.plugins.rti.ncdf.NcdfFileInspector'
        """
        check_is_a_string(fullClassName)
        self._identifier = identifier
        self._fullClassName = fullClassName
        self._cls = None # The underlying class. Not yet imported.
        self._triedImport = False
        self._exception = None # Any exception that occurs during the class import
        

    def __repr__(self):
        return "<{}: {}>".format(type_name(self), self.identifier)
    
    @property
    def identifier(self):
        """ Identifier comprising of library and name, separated by a slash.
            Can contain spaces. E.g.: 'library name/My Widget'
            Must be unique when spaces are removed and converted to lower case. 
        """
        return self._identifier

    @property
    def name(self):
        """ The last part of the identifier.
        """
        return os.path.basename(self._identifier)

    @property
    def library(self):
        """ The identifier minus the last part (the name).
            Used to group libraries together, for instance in menus. 
        """
        return os.path.dirname(self._identifier)

    @property
    def fullClassName(self):
        """ full name of the underlying class. 
            E.g.: 'libargos.plugins.rti.ncdf.NcdfFileInspector'
        """
        return self._fullClassName

    @property
    def className(self):
        """ The name of the underlying class. Is the last part of the fullClassName.
        """
        return self.fullClassName.rsplit('.', 1)[1]

    @property
    def cls(self):
        """ Returns the underlying class. 
            Returns None if the class was not imported or import failed.
        """
        return self._cls
    
    @property
    def docString(self):
        """ A cleaned up version of the doc string of the registered class. 
            Can serve as backup in case descriptionHtml is empty.
        """
        return inspect.cleandoc('' if self.cls is None else self.cls.__doc__) 

    @property
    def triedImport(self):
        """ Returns True if the class has been imported (either successfully or not) 
        """
        return self._triedImport

    @property
    def successfullyImported(self):
        """ Returns True if the import was a success, False if an exception was raised.
            Returns None if the class was not yet imported.
        """
        if self.triedImport:
            return self.exception is None
        else:
            return None            
    
    @property
    def exception(self):
        """ The exception that occurred during the class import. 
            Returns None if the import was successful.
        """
        return self._exception
    
    
    def tryImportClass(self):
        """ Tries to import the registered class. 
            Will set the exception property if and error occurred.
        """
        self._triedImport = True
        self._exception = None
        self._cls = None
        try:
            self._cls = import_symbol(self.fullClassName) # TODO: check class?
        except Exception as ex:
            self._exception = ex


    def getClass(self, tryImport=True):
        """ Gets the underlying class. Tries to import if tryImport is True (the default).
            Returns None if the import has failed (the exception property will contain the reason)
        """
        if not self.triedImport and tryImport:
            self.tryImportClass()
            
        return self._cls



class BaseRegistry(object):
    """ Class that maintains the collection of registered classes.
        Each class has an identifier that must be unique in lower-case with spaces are removed.
    """
    def __init__(self):
        """ Constructor
        """
        self._registeredClasses = {}
    

    def registeredClasses(self):
        """ The registered classes. To be used as read-only.
        """
        return [value for _key, value in self.registeredItems()]
            

    def registeredItems(self):
        """ The registered items (keys, class) tuples. To be used as read-only.
        """
        return sorted(self._registeredClasses.items())
    
            
    def addRegisteredClass(self, registeredClass):
        """ Adds a RegisteredClass object to the registry.
        """
        check_class(registeredClass, RegisteredClass)
        key = registeredClass.identifier
        
        if key in self._registeredClasses:
            oldRegClass = self._registeredClasses[key]
            raise KeyError("Class key {} already registered as {}"
                           .format(key, oldRegClass.fullClassName))
            
        logger.info("Registering {!r} with {}".format(key, registeredClass.fullClassName))
        self._registeredClasses[key] = registeredClass

