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

""" Contains the ConfigItemDelegate class.
"""
from __future__ import print_function

import logging
from argos.config.abstractcti import InvalidInputError
from argos.qt import Qt, QtCore, QtWidgets
from argos.qt.misc import widgetSubCheckBoxRect
from argos.widgets.constants import TREE_CELL_SIZE_HINT

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901

class ConfigItemDelegate(QtWidgets.QStyledItemDelegate):
    """ Provides editing facilities for config tree items.
        Creates an editor kd on the underlying config tree item at an index.

        We don't use a QItemEditorFactory since that is typically registered for a type of
        QVariant. We then would have to make a new UserType QVariant for (each?) CTI.
        This is cumbersome and possibly unPyQTtonic :-)
    """
    def __init__(self, parent=None):
        super(ConfigItemDelegate, self).__init__(parent=parent)

        self.commitData.connect(self._prepareCommit)


    def createEditor(self, parent, option, index):
        """ Returns the widget used to change data from the model and can be reimplemented to
            customize editing behavior.

            Reimplemented from QStyledItemDelegate.
        """
        logger.debug("ConfigItemDelegate.createEditor, parent: {!r}".format(parent.objectName()))
        assert index.isValid(), "sanity check failed: invalid index"

        cti = index.model().getItem(index)
        editor = cti.createEditor(self, parent, option)
        return editor


    def finalizeEditor(self, editor):
        """ Calls editor.finalize().

            Not part of the QAbstractItemView interface but added to be able to free resources.

            Note that, unlike the other methods of this class, finalizeEditor does not have an
            index parameter. We cannot derive this since indexForEditor is a private method in Qt.
            Therefore a AbstractCtiEditor maintains a reference to its config tree item (cti).
        """
        editor.finalize()


    def _prepareCommit(self, editor):
        """ Called when commitData signal is emitted. Calls the prepareCommit of the editor.
        """
        editor.prepareCommit()


    def setEditorData(self, editor, index):
        """ Provides the widget with data to manipulate.
            Calls the setEditorValue of the config tree item at the index.

            :type editor: QWidget
            :type index: QModelIndex

            Reimplemented from QStyledItemDelegate.
        """
        # We take the config value via the model to be consistent with setModelData
        data = index.model().data(index, Qt.EditRole)
        editor.setData(data)


    def setModelData(self, editor, model, index):
        """ Gets data from the editor widget and stores it in the specified model at the item index.
            Does this by calling getEditorValue of the config tree item at the index.

            :type editor: QWidget
            :type model: ConfigTreeModel
            :type index: QModelIndex

            Reimplemented from QStyledItemDelegate.
        """
        try:
            data = editor.getData()
        except InvalidInputError as ex:
            logger.warn(ex)
        else:
            # The value is set via the model so that signals are emitted
            logger.debug("ConfigItemDelegate.setModelData: {}".format(data))
            model.setData(index, data, Qt.EditRole)


    def updateEditorGeometry(self, editor, option, index):
        """ Ensures that the editor is displayed correctly with respect to the item view.
        """
        cti = index.model().getItem(index)
        if cti.checkState is None:
            displayRect = option.rect
        else:
            checkBoxRect = widgetSubCheckBoxRect(editor, option)
            offset = checkBoxRect.x() + checkBoxRect.width()
            displayRect = option.rect
            displayRect.adjust(offset, 0, 0, 0)

        editor.setGeometry(displayRect)


