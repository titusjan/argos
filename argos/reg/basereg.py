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
"""
import enum
import logging, inspect, os, sys
import traceback

from argos.info import DEBUGGING
from argos.utils.cls import import_symbol, check_is_a_string, type_name, check_class
from argos.reg.tabmodel import BaseItem, BaseItemStore, BaseTableModel
from argos.qt import Qt, QtGui
from argos.utils.misc import string_to_identifier

logger = logging.getLogger(__name__)


QCOLOR_REGULAR = QtGui.QColor('black')
QCOLOR_NOT_IMPORTED = QtGui.QColor('grey')
QCOLOR_ERROR = QtGui.QColor('red')

# Used to determine the type of editor needed
@enum.unique
class RegType(enum.Enum):
    String = 0
    ColorStr = 1
    ShortCut = 2


def nameToIdentifier(fullName):
    """ Constructs the regItem identifier given its full name
    """
    return string_to_identifier(fullName, white_space_becomes='')


class BaseRegItem(BaseItem):
    """ Represents a class that is registered in the registry.

        Each registry item (RegItem) can import its class. If the import fails, the exception info
        is put into the exception property. The underlying class is not imported by default;
        use tryImportClass or getClass() for this.

        Some of the underlying class's attributes, such as the docstring, are made available as
        properties of the RegItem as well. If the class is not yet imported, they return None.
    """
    FIELDS = ['name', 'absClassName', 'pythonPath']
    TYPES = [RegType.String, RegType.String, RegType.String]
    LABELS = ['Name', 'Class', 'Python path']
    STRETCH = [False, False, True]

    def __init__(self, name='', absClassName='', pythonPath=''):
        """ Constructor.

            :param name: fullName comprising of library and name, separated by a slash.
                Can contain spaces. E.g.: 'library name/My Widget'
                Must be unique when spaces are removed and converted to lower case.
            :param absClassName: absolute name of the underlying class. Must include the full
                path of packages and module. E.g.: 'argos.plugins.rti.ncdf.NcdfFileInspector'
            :param pythonPath: directory that will be added to the sys.path before importing.
                Can be multiple directories separated by a colon (:)
        """
        super(BaseRegItem, self).__init__()

        self._data = {'name': name, 'absClassName': absClassName, 'pythonPath': pythonPath}

        self._cls = None # The underlying class. Not yet imported.
        self._triedImport = False
        self._exception = None # Any exception that occurs during the class import


    def __repr__(self):
        return "<{} (Ox{:x}): {!r}>".format(type_name(self), id(self), self.name)


    @property
    def identifier(self):
        """ Identifier. Should be unique.

            Is the name with white space removed.
        """
        return nameToIdentifier(self._data['name'])


    @property
    def name(self):
        """ Name of the registered plug in.
        """
        return self._data['name']


    @property
    def absClassName(self):
        """ Absolute name of the underlying class.

        Must include the full path of packages and module.
        E.g.: 'argos.plugins.rti.ncdf.NcdfFileInspector'
        """
        return self._data['absClassName']


    @property
    def pythonPath(self):
        """ Directory that will be added to the sys.path before importing.
            Can be multiple directories separated by a colon (:)
        """
        return self._data['pythonPath']


    @property
    def library(self):
        """ The fullName minus the last part (the name).
            Used to group libraries together, for instance in menus.
        """
        return os.path.dirname(self.absClassName)


    def splitName(self):
        """ Returns (self.library, self.name) tuple but is more efficient than calling both
            properties separately.
        """
        return os.path.split(self.absClassName)


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

    @triedImport.setter
    def triedImport(self, value):
        """ Set to true if the class has been imported (either successfully or not)
        """
        self._triedImport = value


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
        logger.debug("Importing: {}".format(self.absClassName))
        self._triedImport = True
        self._exception = None
        self._cls = None
        try:
            for pyPath in self.pythonPath.split(';'):
                if pyPath and pyPath not in sys.path:
                    logger.debug("Appending {!r} to the PythonPath.".format(pyPath))
                    sys.path.append(pyPath)
            self._cls = import_symbol(self.absClassName)
        except Exception as ex:
            # Add traceback in human readable form to the exception for later printing.
            # This is a hack for Python-2 to store the traceback later use. See https://stackoverflow.com/a/11415140/
            ex.traceBackString = traceback.format_exc()
            self._exception = ex
            logger.warning("Unable to import {!r}: {}".format(self.absClassName, ex))
            logger.debug("Traceback: {}".format(ex.traceBackString))


    def getClass(self, tryImport=True):
        """ Gets the underlying class. Tries to import if tryImport is True (the default).
            Returns None if the import has failed (the exception property will contain the reason)
        """
        if not self.triedImport and tryImport:
            self.tryImportClass()

        return self._cls



class BaseRegistry(BaseItemStore):
    """ Class that maintains the collection of registered classes (plugins).

        It can load or store its classes in the persistent settings. It can also create a default
        set of plugins that can be used initially, the first time the program is executed.

        The BaseRegistry can only store items of one type (ClassRegItem). Descendants will
        store their own type. For instance the InspectorRegistry will store InspectorRegItem
        items. This makes serialization easier.
    """
    ITEM_CLASS = BaseRegItem

    @property
    def registryName(self):
        """ # Human readable name for this registry. Please override.
        """
        raise NotImplementedError()


    def getItemById(self, identifier):
        """ Gets a registered item given its identifier. Returns None if not found.
        """
        #logger.debug("Searching for '{}' in items".format(identifier))
        for item in self._items:
            #logger.debug("    Item: {}".format(item.identifier))
            if item.identifier == identifier:
                return item

        return None


    def getDefaultItems(self):
        """ Returns a list with the default plugins in the registry.
            This is used initialize the application plugins when there are no saved settings,
            for instance the first time the application is started.
            The base implementation returns an empty list but other registries should override it.
        """
        raise NotImplementedError


    def createTableModel(self, parent=None):
        """ Creates a BaseRegistryModel that has self as an item store.

            Descendants can override so they can create specialized types of registry models
        """
        return BaseRegistryModel(store=self, parent=parent)



class BaseRegistryModel(BaseTableModel):
    """ Table model that holds a BaseRegistry store
    """

    def __init__(self, store, parent=None):
        """ Constructor.

            :param store: Underlying data store, must descent from BaseRegistry
            :param parent: Parent widget
        """
        super(BaseRegistryModel, self).__init__(store, parent)
        check_class(store, BaseRegistry)

        self.regularBrush = QtGui.QBrush(QCOLOR_REGULAR)
        self.notImportedBrush = QtGui.QBrush(QCOLOR_NOT_IMPORTED)
        self.errorBrush = QtGui.QBrush(QCOLOR_ERROR)


    def data(self, index, role=Qt.DisplayRole):
        """ Returns the data stored under the given role for the item referred to by the index.
        """
        if not index.isValid():
            return None

        if role == Qt.ForegroundRole:
            item = self._store.items[index.row()]

            if item.successfullyImported is None:
                return self.notImportedBrush
            elif item.successfullyImported:
                return self.regularBrush
            else:
                return self.errorBrush
        else:
            return super(BaseRegistryModel, self).data(index, role=role)


    def setData(self, index, value, role=Qt.EditRole):
        """ Sets the role data for the item at index to value.
        """
        result = super(BaseRegistryModel, self).setData(index, value, role=role)

        if not index.isValid():
            return False

        if role != Qt.EditRole:
            return False

        regItem = self._store.items[index.row()]
        regItem.tryImportClass()

        self.emitDataChanged(regItem)
        return result


    def tryImportRegItem(self, regItem):
        """ Tries to import a registry item (plugin)
        """
        check_class(regItem, self.store.ITEM_CLASS)
        logger.debug("Importing {}...".format(regItem.name))
        regItem.tryImportClass()
        self.emitDataChanged(regItem)
