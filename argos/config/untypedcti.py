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

""" Contains the UntypedCti and UntypedCtiEditor classes
"""
import logging

from argos.config.abstractcti import AbstractCti, AbstractCtiEditor
from argos.qt import QtWidgets, Qt

logger = logging.getLogger(__name__)



class UntypedCti(AbstractCti): # TODO: rename to ReadOnlyCti?
    """ Config Tree Item to store a any type of data as long as it can be edited with a QLineEdit.

        Typically it's better to use 'typed' CTIs, where the data is always internally stored in
        the same type (enforced by _enforceDataType).

        This item is non-editable and can, for instance, be used for introspection.
    """
    def __init__(self, nodeName, defaultData='', doc=''):
        """ Constructor. For the parameters see the AbstractCti constructor documentation.
        """
        super(UntypedCti, self).__init__(nodeName, defaultData)
        self.doc = doc # TODO: all CTIs

    def _enforceDataType(self, value):
        """ Since UntypedCti can store any type of data no conversion will be done.
        """
        return value

    def createEditor(self, delegate, parent, option):
        """ Creates an UntypedCtiEditor.
            For the parameters see the AbstractCti constructor documentation.
            Note: since the item is not editable this will never be called.
        """
        return UntypedCtiEditor(self, delegate, parent=parent)

    @property
    def valueColumnItemFlags(self):
        """ Returns the flags determine how the user can interact with the value column.
            Returns Qt.NoItemFlags so that the item is not editable
        """
        return Qt.NoItemFlags


class UntypedCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a QLineEdit for editing UntypedCti objects.

        Only
    """
    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters
        """
        super(UntypedCtiEditor, self).__init__(cti, delegate, parent=parent)
        self.lineEditor = self.addSubEditor(QtWidgets.QLineEdit(), isFocusProxy=True)

    def setData(self, data):
        """ Provides the main editor widget with a data to manipulate.
        """
        self.lineEditor.setText(str(data))

    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.lineEditor.text()


