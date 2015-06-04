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

""" Classes for registering plugins. 
    This is part of the libargos.qt package since it uses QSettings for persistency. 
"""

import logging, inspect, os, ast

from libargos.qt import QtCore
from libargos.utils.cls import import_symbol, check_is_a_string, type_name, check_class

logger = logging.getLogger(__name__)


class RegisteredClassItem(object):
    """ Represents an class that is registered in the registry. Each class has an identifier that
        must be unique and a fullClassName with name the class (inclusive package and module part).
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
    def descriptionHtml(self):
        """ HTML help describing the class. For use in the detail editor.
        """
        if self.cls is None:
            return None
        elif hasattr(self.cls, 'descriptionHtml'):
            return self.cls.descriptionHtml()
        else:
            return ''
    

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
        logger.debug("......Importing: {}".format(self.fullClassName))
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

    @classmethod
    def createFromDict(cls, dct):
        """ Create an object of type cls with the dct as the kwargs
        """
        return cls(**dct)
        
    def asDict(self):
        """ Returns a dictionary for serialization. We don't use JSON since all items are
            quite simple and the registry will always contain the same type of RegisteredClassItem
        """
        return {'identifier': self.identifier, 'fullClassName': self.fullClassName}


class ClassRegistry(object):
    """ Class that maintains the collection of registered classes.
        Each class has an identifier that must be unique in lower-case with spaces are removed.
        
        The ClassRegistry can only store items of one type (RegisteredClassItem). Descendants will
        store their own type. For instance the InspectorRegistry will store RegisteredInspector 
        items. This makes serialization easier.
        
        An optional QSettings group name can be specified so that the registry knows where to 
        load/store its settings. This can also be specified with the method parameters.
    """
    def __init__(self, settingsGroupName=None):
        """ Constructor
        """
        self.settingsGroupName = settingsGroupName
        
        # We use an list to store the items in order and an index to find them in O(1)
        # We cannot use an ordereddict for this as this uses linked-list internally and therefore
        # does not allow to retrieve the Nth element in O(1) 
        self._items = []
        self._index = {}
        
        # The registry can only contain items of this type.
        self._itemClass = RegisteredClassItem
    
    
    @property
    def items(self):
        """ The registered class items. Use as read-only
        """
        return self._items    
            
    
    def clear(self):
        """ Empties the registry
        """
        self._items = []
        self._index = {}
        
    
    def getItemById(self, identifier):
        """ Gets a registered item given its identifier.
        """
        return self._index[identifier]

            
    def registerItem(self, item):
        """ Adds a RegisteredClassItem object to the registry.
        """
        check_class(item, RegisteredClassItem)
        key = item.identifier
        
        if key in self._index:
            oldRegClass = self._index[key]
            raise KeyError("Class key {} already registered as {}"
                           .format(key, oldRegClass.fullClassName))
            
        logger.info("Registering {!r} with {}".format(key, item.fullClassName))
        self._items.append(item)
        self._index[key] = item

            
    def removeItem(self, item):
        """ Removes a RegisteredClassItem object to the registry.
            Will raise a KeyError if the item is not registered.
        """
        check_class(item, RegisteredClassItem)
        key = item.identifier
            
        logger.info("Removing {!r} with {}".format(key, item.fullClassName))
        
        del self._index[key]
        idx = self._items.find(item)
        del self._items[idx]


    def loadOrInitSettings(self, groupName=None):
        """ Reads the registry items from the persistent settings store, falls back on the 
            default plugins if there are not settings in the store for this registry.
            It there 
        """ 
        groupName = groupName if groupName else self.settingsGroupName
        settings = QtCore.QSettings()
        
        if settings.contains(groupName):
            self.loadSettings(groupName)
        else:
            logger.info("Group {!r} not found, falling back on default settings".format(groupName))
            for item in self.getDefaultItems():
                self.registerItem(item)
            self.saveSettings(groupName)


    def loadSettings(self, groupName=None):
        """ Reads the registry items from the persistent settings store.
        """ 
        groupName = groupName if groupName else self.settingsGroupName
        settings = QtCore.QSettings()
        logger.info("Reading {!r} from: {}".format(groupName, settings.fileName()))
        
        settings.beginGroup(groupName)
        self.clear()
        try:
            for key in settings.childKeys():
                if key.startswith('item'):
                    dct = ast.literal_eval(settings.value(key))
                    regItem = self._itemClass.createFromDict(dct)
                    self.registerItem(regItem)
        finally:
            settings.endGroup()
            
            
    def saveSettings(self, groupName=None):
        """ Writes the registry items into the persistent settings store.
        """
        groupName = groupName if groupName else self.settingsGroupName
        settings = QtCore.QSettings()
        logger.info("Saving {} to: {}".format(groupName, settings.fileName()))
        
        settings.remove(groupName) # start with a clean slate
        settings.beginGroup(groupName)
        try:
            for itemNr, item in enumerate(self.items):
                key = "item-{:03d}".format(itemNr)
                value = repr(item.asDict())
                settings.setValue(key, value)
        finally:
            settings.endGroup()
            
            
    def getDefaultItems(self):
        """ Returns a list with the default plugins in the registry. 
            This is used initialize the application plugins when there are no saved settings, 
            for instance the first time the application is started.
            The base implementation returns an empty list but other registries should override it.
        """
        return []
            
            