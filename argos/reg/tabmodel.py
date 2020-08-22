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

""" The table model classes that form the base of the registries
"""

import logging

from argos.utils.cls import type_name, check_class

from argos.qt import QtCore, QtSignal, Qt


logger = logging.getLogger(__name__)


class BaseItem(object):
    """ An object that is stored in the BaseItemStore.

        It always must have a name, which is used as the identifier
    """
    FIELDS = []  # The fields that this item contains.
    LABELS = []  # Human readable label for each field. Should be overridden in descendants
    STRETCH = [] # True -> the corresponding table column can stretch. False -> resize to contents.

    # For debugging...
    # FIELDS = ['debugCount', 'name', 'path']
    # LABELS = FIELDS # For debugging.
    # STRETCH = [True, False, True]

    COL_DECORATION = None   # Column number that contains the decoration. None for no icons

    _sequenceCounter = 0  # For debugging

    def __init__(self, **kwargs):
        """ Constructor
        """
        self._data = {}

        # Set fields from keyword args
        for key, value in kwargs.items():
            if key not in self.FIELDS:
                raise ValueError("Key '{}' not in field names: {}".format(key, self.FIELDS))
            self._data[key] = value

        # Set remaining fields to empty string
        for key in self.FIELDS:
            if key not in self._data:
                if key == 'debugCount':
                    self._data['debugCount'] = BaseItem._sequenceCounter
                    BaseItem._sequenceCounter += 1
                else:
                    self._data[key] = ''

        assert len(self.FIELDS) > 0
        if len(self.LABELS) != len(self.FIELDS):
            raise AssertionError("Number of labels ({}) is not equal to number of fields ({})"
                                 .format(len(self.LABELS), len(self.FIELDS)))

        if len(self.STRETCH) != len(self.FIELDS):
            raise AssertionError("Number of stretches ({}) is not equal to number of labels ({})"
                                 .format(len(self.STRETCH), len(self.FIELDS)))



    def __repr__(self):
        return "<{}: {}>".format(type_name(self), self._data)


    @property
    def data(self):
        """ The data dictionary
        """
        return self._data


    @property
    def decoration(self):
        """ A optional icon that is displayed in the COL_DECORATION column.

            The base implementation returns None (no icon). Descendants can override this
        """
        return None


    #####
    # The follow functions load or save their state to JSON config files.
    #####

    def marshall(self):
        """ Returns a dictionary to save in the persistent settings
        """
        cfg = {}
        for field in self.FIELDS:
            cfg[field] = str(self._data[field])

        return cfg


    def unmarshall(self, cfg):
        """ Initializes itself from a config dict form the persistent settings.
        """
        self._fields = {}
        for field in self.FIELDS:
            if field in cfg:
                self._data[field] = cfg[field]
            else:
                logger.warning("Field '{}' not in config: {}".format(field, cfg))



class BaseItemStore(object):
    """ Class that stores a collection of BaseItems or descendants. Base class for the registries.

        In principle this class could be merged with the BaseItemModel but I chose to separate them
        because most of the time the data is used read-only, from the store. Only when the user
        edits the registry from the GUI is a table model needed. This way registries don't descent
        from QAbstractTableModel and inherit a huge number of methods.

        The BaseItemStore can only store items of one type (ITEM_CLASS). Descendants will
        store their own type. For instance the InspectorRegistry will store InspectorstoreItem
        items. This makes serialization easier.
    """

    # All items in this store will be of this class. BaseModel descendant will typically override
    # the ITEM_CLASS value
    ITEM_CLASS = BaseItem

    def __init__(self):
        """ Constructor
        """
        self._items = []


    def __str__(self):
        return "Item store"

    @property
    def fieldNames(self):
        """ Name of the fields. So think twice before changing them."""
        return self.ITEM_CLASS.FIELDS


    @property
    def fieldLabels(self):
        """ Short, human readable, label fields for use in GUI. """
        return self.ITEM_CLASS.LABELS


    @property
    def canStretchPerColumn(self):
        """ List of booleans, for each column indicating if it can strech.
            True -> the corresponding table column can stretch. False -> resize to contents.
        """
        return self.ITEM_CLASS.STRETCH


    @property
    def items(self):
        """ The registered class items.
        """
        return self._items


    def clear(self):
        """ Empties the registry
        """
        self._items = []


    #####
    # The follow functions load or save their state to JSON config files.
    #####

    def marshall(self):
        """ Returns a dictionary to save in the persistent settings
        """
        return [item.marshall() for item in self.items]


    def unmarshall(self, cfg):
        """ Initializes itself from a config dict form the persistent settings.
        """
        self.clear()
        if not cfg:
            logger.info("Empty config, using registry defaults for: {}".format(self))
            for storeItem in self.getDefaultItems():
                self._items.append(storeItem)
        else:
            for dct in cfg:
                logger.debug("Creating {} from: {}".format(self.ITEM_CLASS, dct))
                storeItem = self.ITEM_CLASS()
                storeItem.unmarshall(dct)
                self._items.append(storeItem)


    def getDefaultItems(self):
        """ Returns a list with the default items.
            This is used initialize the application plugins when there are no saved settings,
            for instance the first time the application is started.
            The base implementation returns an empty list but other registries should override it.
        """
        return []



# Rhe main window inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201


class BaseTableModel(QtCore.QAbstractTableModel):

    sigItemChanged = QtSignal(BaseItem) # An item has changed.

    def __init__(self, store, parent=None):
        """ Constructor.

            :param store: Underlying data store, must descent from BaseItemStore
            :param parent: Parent widget
        """
        super(BaseTableModel, self).__init__(parent)
        check_class(store, BaseItemStore)
        self._store = store
        self._fieldNames = self._store.fieldNames
        self._fieldLabels = self.store.fieldLabels

    @property
    def store(self):
        """ The underlying BaseItemStore

            Note that if you modify this directly (i.e. not via the setData method), the model is
            not aware of the modifications. Therefore the user is responsible for nofifying the
            this table model after modifications.
        """
        return self._store


    def rowCount(self, parent=None):
        """ Returns the number of items in the registry."""
        return len(self._store.items)


    def columnCount(self, parent=None):
        """ Returns the number of columns of the registry."""
        return len(self._fieldNames)


    def itemFromIndex(self, index, altItem=None):
        """ Gets the item given the model index
            Returns altItem (default: None) if the index is not alid
        """
        if not index.isValid():
            return altItem
        else:
            return self._store.items[index.row()]


    def indexFromItem(self, storeItem, col=0):
        """ Gets the index (with column=0) for the row that contains the storeItem
            If col is negative, it is counted from the end
        """
        if col < 0:
            col = len(self._fieldNames) - col
        try:
            row = self._store.items.index(storeItem)
        except ValueError:
            return QtCore.QModelIndex()
        else:
            return self.index(row, col)


    def flags(self, index):
        """ Returns the item flags for the given index.
        """
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def headerData(self, section, orientation, role):
        """ Returns the header for a section (row or column depending on orientation).
            Reimplemented from QAbstractTableModel to make the headers start at 0.
        """
        if role == QtCore.Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._fieldLabels[section]
            else:
                return str(section)
        else:
            return None


    def data(self, index, role=Qt.DisplayRole):
        """ Returns the data stored under the given role for the item referred to by the index.
        """
        if not index.isValid():
            return None

        if role not in (Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole, Qt.DecorationRole):
            return None

        row = index.row()
        col = index.column()
        item = self._store.items[row]
        attrName = self._fieldNames[col]

        if role in (Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole):
            return str(item.data[attrName])

        elif role == Qt.DecorationRole:
            if col == item.COL_DECORATION:
                return item.decoration

        # elif role == Qt.ForegroundRole:
        #     return self.regularBrush
        else:
            raise ValueError("Invalid role: {}".format(role))


    def setData(self, index, value, role=Qt.EditRole):
        """ Sets the role data for the item at index to value.
        """
        if not index.isValid():
            return False

        if role != Qt.EditRole:
            return False

        row = index.row()
        col = index.column()
        storeItem = self._store.items[row]
        fieldName = self._fieldNames[col]
        storeItem.data[fieldName] = value

        self.emitDataChanged(storeItem)

        return True


    def emitDataChanged(self, storeItem):
        """ Emits the dataChanged and sigItemChanged signals for the storeItem
        """
        leftIndex = self.indexFromItem(storeItem, col=0)
        rightIndex = self.indexFromItem(storeItem, col=-1)

        logger.debug("Data changed: {} ... {}".format(self.data(leftIndex), self.data(rightIndex)))
        self.dataChanged.emit(leftIndex, rightIndex)
        self.sigItemChanged.emit(storeItem)


    def createItem(self):
        """ Creates an emtpy item of type ITEM_CLASS
        """
        return self.store.ITEM_CLASS()


    def insertItem(self, item, row):
        """ Insert an item in the store at a certain row.
        """
        check_class(item, self.store.ITEM_CLASS)
        logger.info("Inserting {!r} at row {}".format(item, row, self))
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        try:
            self.store.items.insert(row, item)
        finally:
            self.endInsertRows()


    def popItemAtRow(self, row):
        """ Removes a store item from the store.
            Returns the item
        """
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        try:
            item = self.store.items[row]
            del self.store.items[row]
            return item
        finally:
            self.endRemoveRows()


    def moveItem(self, fromRow, toRow):
        """ Moves the item for position
        """
        item = self.popItemAtRow(fromRow)

        # This always works, regardless if fromPos is before or after toPos
        self.insertItem(item, toRow)




def main():
    """ Test classes
    """
    from pprint import pprint

    store2 = BaseItemStore()
    store2.unmarshall("[{'name': '0'}, {'name': 'A'},  {'name': 'b'},  {'name': 'b'},  "
                      "{'name': 'B'},  {'name': 'C'}]")

    print("Store2")
    pprint(store2)




if __name__ == "__main__":
    main()
