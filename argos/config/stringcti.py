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

""" Contains the StringCti and StringCtiEditor classes
"""
import logging

from argos.config.abstractcti import AbstractCti, AbstractCtiEditor
from argos.qt import QtWidgets

logger = logging.getLogger(__name__)


class StringCti(AbstractCti):
    """ Config Tree Item to store a string. It can be edited with a QLineEdit.
        The string can have an optional maximum length.
    """
    def __init__(self, nodeName, defaultData='', maxLength=None):
        """ For the (other) parameters see the AbstractCti constructor documentation.

            :param maxLength: maximum length of the string
        """
        super(StringCti, self).__init__(nodeName, defaultData)

        # We could define a mask here as well but since that very likely will be rarely used,
        # we don't want to store it for each cti. You can make a subclass if you need it.
        self.maxLength = maxLength

    def _enforceDataType(self, data):
        """ Converts to str so that this CTI always stores that type.
        """
        return str(data)

    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return "maxLength = {}".format(self.maxLength)

    def createEditor(self, delegate, parent, option):
        """ Creates a StringCtiEditor.
            For the parameters see the AbstractCti constructor documentation.
        """
        return StringCtiEditor(self, delegate, parent=parent)



class StringCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a QLineEdit for editing StringCti objects.
    """
    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters
        """
        super(StringCtiEditor, self).__init__(cti, delegate, parent=parent)
        self.lineEditor = self.addSubEditor(QtWidgets.QLineEdit(), isFocusProxy=True)

        if cti.maxLength is not None:
            self.lineEditor.setMaxLength(cti.maxLength)


    def setData(self, data):
        """ Provides the main editor widget with a data to manipulate.
        """
        self.lineEditor.setText(str(data))


    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.lineEditor.text()

