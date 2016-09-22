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

""" Text widget inspector.
"""
import logging

from libargos.config.groupcti import MainGroupCti, GroupCti
from libargos.config.choicecti import ChoiceCti
from libargos.config.qtctis import FontCti
from libargos.inspector.abstract import AbstractInspector
from libargos.qt import QtGui
from libargos.utils.cls import to_string, check_class

logger = logging.getLogger(__name__)


class TextInspectorCti(MainGroupCti):
    """ Configuration tree item for a TextInspectorCti inspector
    """
    def __init__(self, textInspector, nodeName):
        """ Constructor

            :param textInspector: the TextInspector widget that is being configured
            :param nodeName: node name
        """
        super(TextInspectorCti, self).__init__(nodeName)

        check_class(textInspector, TextInspector)
        self.textInspector = textInspector

        Opt = QtGui.QTextOption
        self.wordWrapCti = self.insertChild(
            ChoiceCti('word wrap',
                      displayValues=['No wrapping', 'Word boundaries', 'Anywhere',
                                     'Boundaries or anywhere'],
                      configValues=[Opt.NoWrap, Opt.WordWrap, Opt.WrapAnywhere,
                                    Opt.WrapAtWordBoundaryOrAnywhere]))

        self.encodingCti = self.insertChild(
            ChoiceCti('encoding', editable=True,
                      configValues=['utf-8', 'ascii', 'latin-1', 'windows-1252']))

        self.fontCti = self.insertChild(FontCti(self.textInspector.editor, "font",
                                                defaultData=QtGui.QFont('Courier', 14)))


class TextInspector(AbstractInspector):
    """ Inspector that contains a QPlainTextEdit that shows one element at the time.

        This is usefull when the data under inspection ia a (large) text.
        Can optionally reformat the data if it is an XML or JSON string.
    """
    def __init__(self, collector, parent=None):

        super(TextInspector, self).__init__(collector, parent=parent)

        self.editor = QtGui.QPlainTextEdit()
        self.editor.setReadOnly(True)

        self.contentsLayout.addWidget(self.editor)

        self._config = self._createConfig()


    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.

            Returns an empty tuple; the data under inspection is zero-dimensional.
        """
        return tuple()


    def _createConfig(self):
        """ Creates a config tree item (CTI) hierarchy containing default children.
        """
        return TextInspectorCti(textInspector=self, nodeName='inspector')


    def _drawContents(self, reason=None, initiator=None):
        """ Converts the (zero-dimensional) sliced array to string and puts it in the text editor.

            The reason and initiator parameters are ignored.
            See AbstractInspector.updateContents for their description.
        """
        logger.debug("TextInspector._drawContents: {}".format(self))
        self.editor.clear()

        slicedArray = self.collector.getSlicedArray()

        if slicedArray is None:
            return

        # Sanity check, the slicedArray should be zero-dimensional. It can be used as a scalar.
        # In fact, using an index (e.g. slicedArray[0]) will raise an exception.
        assert slicedArray.data.ndim == 0, \
            "Expected zero-dimensional array. Got: {}".format(slicedArray.ndim)

        # Valid data from here...
        slicedScalar = slicedArray.data[()] # Convert to Numpy scalar
        isMasked = slicedArray.mask[()]

        text = to_string(slicedScalar, masked=isMasked, maskFormat='--',
                         decode_bytes=self.config.encodingCti.configValue)
        self.editor.setPlainText(text)
        self.editor.setWordWrapMode(self.config.wordWrapCti.configValue)

        # Update the editor font from the font config item (will call self.editor.setFont)
        self.config.updateTarget()
