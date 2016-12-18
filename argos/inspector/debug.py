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

""" Debug inspector.
"""
import logging

from argos.info import DEBUGGING
from argos.config.groupcti import MainGroupCti, GroupCti
from argos.inspector.abstract import AbstractInspector
from argos.qt import Qt, QtGui, QtWidgets

logger = logging.getLogger(__name__)


class DebugInspector(AbstractInspector):
    """ Empty inspector, mainly for debugging purposes.
    """
    def __init__(self, collector, parent=None):

        super(DebugInspector, self).__init__(collector, parent=parent)

        self.label = QtWidgets.QLabel()
        self.label.setWordWrap(True)
        self.contentsLayout.addWidget(self.label)

        self._config = self._createConfig()


    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple()


    def _createConfig(self):
        """ Creates a config tree item (CTI) hierarchy containing default children.
        """
        rootItem = MainGroupCti('debug inspector')

        if DEBUGGING:
            # Some test config items.
            import numpy as np
            from argos.config.untypedcti import UntypedCti
            from argos.config.stringcti import StringCti
            from argos.config.intcti import IntCti
            from argos.config.floatcti import FloatCti, SnFloatCti
            from argos.config.boolcti import BoolCti, BoolGroupCti
            from argos.config.choicecti import ChoiceCti
            from argos.config.qtctis import PenCti

            grpItem = GroupCti("group")
            rootItem.insertChild(grpItem)

            lcItem = UntypedCti('line color', 123)
            grpItem.insertChild(lcItem)

            disabledItem = rootItem.insertChild(StringCti('disabled', "Can't touch me"))
            disabledItem.enabled=False

            grpItem.insertChild(IntCti('line-1 color', 7, minValue = -5, stepSize=2,
                                       prefix="@", suffix="%", specialValueText="I'm special"))
            rootItem.insertChild(StringCti('letter', 'aa', maxLength = 1))
            grpItem.insertChild(FloatCti('width', 2, minValue =5, stepSize=0.45, decimals=3,
                                         prefix="@", suffix="%", specialValueText="so very special"))
            grpItem.insertChild(SnFloatCti('scientific', defaultData=-np.inf))

            gridItem = rootItem.insertChild(BoolGroupCti('grid', True))
            gridItem.insertChild(BoolCti('X-Axis', True))
            gridItem.insertChild(BoolCti('Y-Axis', False))

            rootItem.insertChild(ChoiceCti('hobbit', 2, editable=True,
                                           configValues=['Frodo', 'Sam', 'Pippin', 'Merry']))
            myPen = QtGui.QPen(QtGui.QColor('#1C8857'))
            myPen.setWidth(2)
            myPen.setStyle(Qt.DashDotDotLine)
            rootItem.insertChild(PenCti('line', False, resetTo=myPen))

        return rootItem


    def _drawContents(self, reason=None, initiator=None):
        """ Draws the table contents from the sliced array of the collected repo tree item.

            The reason and initiator parameters are ignored.
            See AbstractInspector.updateContents for their description.
        """
        logger.debug("DebugInspector._drawContents: {}".format(self))

        slicedArray = self.collector.getSlicedArray()
        if slicedArray is None:
            text = "<None>"
        else:
            text = ("data = {!r}, masked = {!r}, fill_value = {!r} (?= {}: {})"
                    .format(slicedArray.data, slicedArray.mask, slicedArray.fill_value,
                            slicedArray.data.item(),
                            slicedArray.data.item() == slicedArray.fill_value))

        logger.debug("_drawContents: {}".format(text))
        logger.debug("_drawContents: {!r}".format(slicedArray))

        if DEBUGGING:
            self.label.setText(text)



