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

""" Defines ToggleColumnMixIn class
"""
from __future__ import print_function

import logging

from argos.qt import QtCore, QtWidgets, Qt

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901

# Don't want to create constructors for this mixin just to satisfy Pylint so
# we disable W0201 (attribute-defined-outside-init)
#pylint: disable=W0201


class ToggleColumnMixIn(object):
    """ Adds actions to a QTableView that can show/hide columns
        by right clicking on the header.

        Has functionality for reading/writing from persitent settings.
    """
    def addHeaderContextMenu(self, checked = None, checkable = None, enabled = None):
        """ Adds the context menu from using header information

            checked can be a header_name -> boolean dictionary. If given, headers
            with the key name will get the checked value from the dictionary.
            The corresponding column will be hidden if checked is False.

            checkable can be a header_name -> boolean dictionary. If given, header actions
            with the key name will get the checkable value from the dictionary. (Default True)

            enabled can be a header_name -> boolean dictionary. If given, header actions
            with the key name will get the enabled value from the dictionary. (Default True)
        """
        checked = checked if checked is not None else {}
        checkable = checkable if checkable is not None else {}
        enabled = enabled if enabled is not None else {}

        horizontal_header = self.horizontalHeader()
        horizontal_header.setContextMenuPolicy(Qt.ActionsContextMenu)

        self.toggle_column_actions_group = QtWidgets.QActionGroup(self)
        self.toggle_column_actions_group.setExclusive(False)
        self.__toggle_functions = []  # for keeping references

        for col in range(horizontal_header.count()):
            column_label = self.model().headerData(col, Qt.Horizontal, Qt.DisplayRole)
            #logger.debug("Adding: col {}: {}".format(col, column_label))
            action = QtWidgets.QAction(str(column_label),
                                   self.toggle_column_actions_group,
                                   checkable = checkable.get(column_label, True),
                                   enabled = enabled.get(column_label, True),
                                   toolTip = "Shows or hides the {} column".format(column_label))
            func = self.__makeShowColumnFunction(col)
            self.__toggle_functions.append(func) # keep reference
            horizontal_header.addAction(action)
            is_checked = checked.get(column_label, not horizontal_header.isSectionHidden(col))
            horizontal_header.setSectionHidden(col, not is_checked)
            action.setChecked(is_checked)
            action.toggled.connect(func)


    def getHeaderContextMenuActions(self):
        """ Returns the actions of the context menu of the header
        """
        return self.horizontalHeader().actions()


    def __makeShowColumnFunction(self, column_idx):
        """ Creates a function that shows or hides a column."""
        show_column = lambda checked: self.setColumnHidden(column_idx, not checked)
        return show_column


    def readViewSettings(self, key, settings=None):
        """ Reads the persistent program settings

            :param key: key where the setting will be read from
            :param settings: optional QSettings object which can have a group already opened.
            :returns: True if the header state was restored, otherwise returns False
        """
        #logger.debug("Reading view settings for: {}".format(key))
        if settings is None:
            settings = QtCore.QSettings()

        horizontal_header = self.horizontalHeader()
        header_restored = horizontal_header.restoreState(settings.value(key))

        # update actions
        for col, action in enumerate(horizontal_header.actions()):
            is_checked = not horizontal_header.isSectionHidden(col)
            action.setChecked(is_checked)

        return header_restored

    def saveProfile(self, key, settings=None):
        """ Writes the view settings to the persistent store
            :param key: key where the setting will be read from
            :param settings: optional QSettings object which can have a group already opened.
        """
        #logger.debug("Writing view settings for: {}".format(key))
        if settings is None:
            settings = QtCore.QSettings()
        settings.setValue(key, self.horizontalHeader().saveState())



class ToggleColumnTableWidget(QtWidgets.QTableWidget, ToggleColumnMixIn):
    """ A QTableWidget where right clicking on the header allows the user to show/hide columns
    """
    pass



class ToggleColumnTableView(QtWidgets.QTableView, ToggleColumnMixIn):
    """ A QTableView where right clicking on the header allows the user to show/hide columns
    """
    pass



class ToggleColumnTreeWidget(QtWidgets.QTreeWidget, ToggleColumnMixIn):
    """ A QTreeWidget where right clicking on the header allows the user to show/hide columns
    """
    def horizontalHeader(self):
        """ Returns the horizontal header (of type QHeaderView).

            Override this if the horizontalHeader() function does not exist.
        """
        return self.header()



class ToggleColumnTreeView(QtWidgets.QTreeView, ToggleColumnMixIn):
    """ A QTreeView where right clicking on the header allows the user to show/hide columns
    """
    def horizontalHeader(self):
        """ Returns the horizontal header (of type QHeaderView).

            Override this if the horizontalHeader() function does not exist.
        """
        return self.header()


#pylint: enable=R0901


