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

""" Contains the Config and GroupCtiEditor classes
"""
import logging

from argos.config.abstractcti import AbstractCti, AbstractCtiEditor
from argos.qt import Qt, QtGui, QtWidgets

logger = logging.getLogger(__name__)




class GroupCti(AbstractCti):
    """ Read only config Tree Item that only stores None. It can be used to group CTIs
    """
    def __init__(self, nodeName, defaultData=None, expanded=True):
        """ Constructor. For the parameters see the AbstractCti constructor documentation.
        """
        super(GroupCti, self).__init__(nodeName, defaultData, expanded=expanded)


    def _enforceDataType(self, data):
        """ Passes the data as is; no conversion.
        """
        return data


    def _dataToString(self, data):
        """ Conversion function used to convert the (default)data to the display value.
            Returns an empty string.
        """
        return ""


    def createEditor(self, delegate, parent, _option):
        """ Creates a hidden widget so that only the reset button is visible during editing.
            :type option: QStyleOptionViewItem
        """
        return GroupCtiEditor(self, delegate, parent=parent)


class GroupCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a hidden widget.
        If the item is editable, the reset button is shown.
    """
    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters
        """
        super(GroupCtiEditor, self).__init__(cti, delegate, parent=parent)

        # Add hidden widget to store editor value
        self.widget = self.addSubEditor(QtWidgets.QWidget())
        self.widget.hide()


    def setData(self, data):
        """ Provides the main editor widget with a data to manipulate.
        """
        # Set the data in the 'editor_data' property of the widget to that getData
        # can pass the same value back into the CTI.
        self.widget.setProperty("editor_data", data)


    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.widget.property("editor_data")



class MainGroupCti(GroupCti):
    """ Read only config Tree Item that only stores None.
        To be used as a high level group (e.g. the inspector group)
        Is the same as a groupCti but drawn as light text on a dark grey back ground
    """
    _backgroundBrush = QtGui.QBrush(QtGui.QColor("#606060")) # create only once
    _foregroundBrush = QtGui.QBrush(QtGui.QColor(Qt.white)) # create only once
    _font = QtGui.QFont()
    _font.setWeight(QtGui.QFont.Bold)

    def __init__(self, nodeName, defaultData=None):
        """ Constructor. For the parameters see the AbstractCti constructor documentation.
        """
        super(MainGroupCti, self).__init__(nodeName, defaultData, expanded=True) # always expand


    @property
    def font(self):
        """ Returns a font for displaying this item's text in the tree.
        """
        return self._font


    @property
    def backgroundBrush(self):
        """ Returns a (dark gray) brush for drawing the background role in the tree.
        """
        return self._backgroundBrush


    @property
    def foregroundBrush(self):
        """ Returns a (white) brush for drawing the foreground role in the tree.
        """
        return self._foregroundBrush



