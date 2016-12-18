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

""" Abstract base classes for modeling data tree items for use in the ConfigTreeModel
"""
import logging, os
from json import JSONEncoder, JSONDecoder, loads, dumps

from argos.info import DEBUGGING, icons_directory
from argos.qt import Qt, QtCore, QtGui, QtWidgets, QtSlot
from argos.qt.treeitems import BaseTreeItem
from argos.utils.cls import get_full_class_name, import_symbol


logger = logging.getLogger(__name__)


# TODO: QCompleter? See demos/spreadsheet/spreadsheetdelegate.py

class InvalidInputError(Exception):
    """ Exception raised when the input is invalid after editing
    """
    pass


#################
# JSON encoding #
#################


def ctiLoads(json_str):
    """ Loads a cti from JSON string """
    return loads(json_str)

def ctiDumps(obj, **kwargs):
    """ Dumps cti as JSON string """
    return dumps(obj, cls=CtiEncoder, **kwargs)


class CtiEncoder(JSONEncoder):
    """ JSON encoder that knows how to encode AbstractCti objects
    """
    def default(self, obj):
        if isinstance(obj, AbstractCti):
            return obj.asJsonDict()
        else:
            return JSONEncoder.default(self, obj)


def jsonAsCti(dct):
    """ Config tree item JSON decoding function. Returns a CTI given a dictionary of attributes.
        The full class name of desired CTI class should be in dct['_class_''].
    """
    if '_class_'in dct:
        full_class_name = dct['_class_'] # TODO: how to handle the full_class_name?
        cls = import_symbol(full_class_name)
        return cls.createFromJsonDict(dct)
    else:
        return dct


class CtiDecoder(JSONDecoder):
    """ Config tree item JSON decoder class. Not strictly necessary (you can use the
        jsonAsCti function as object_hook directly in loads) but since we also have an
        encoder class it feels right to have a decoder as well.
    """
    def __init__(self, *args, **kwargs):
        # The object_hook must be given to the parent constructor since that makes
        # an internal scanner.
        super(CtiDecoder, self).__init__(*args, object_hook = jsonAsCti, **kwargs)


###########
# Classes #
###########

class AbstractCti(BaseTreeItem):
    """ TreeItem for use in a ConfigTreeModel. (CTI = Config Tree Item)

        Abstract class. You must implement the _enforceDataType method that ensures the the data
        is stored internally in the correct type. Also, implement the createEditor method if you
        want you CTI to be editable (which is usually the case). If your CTI is not editable, make
        sure that valueColumnItemFlags does not return Qt.ItemIsEditable to prevent createEditor
        from being called by the delegate.

        Just like the BaseTreeItem every node has a name and a full path that is a slash-separated
        string of the full path leading from the root node to the current node. For instance, the
        path may be '/scale/x', the nodeName in that case is 'x'.

        CTIs are used to store a certain configuration value. It can be queried by the value
        property. The type of this value differs between descendants of AbstractCti, but a sub class
        should always return the same type. For example, the ColorCti.value always returns a
        QColor object. The displayValue returns the string representation for use in the tables;
        by default this returns: str(self.value)

        The underlying data is usually stored in that type as well but this is not necessarily so.
        A ChoiceCti, which represents a combo box, stores a list of choices and an index that is
        actual choice made by the user. ChoiceCti.data contains the index while
        ChoiceCti.configValue returns: choices[index]. Note that the constructor expects the data
        as input parameter. The constructor calls the _enforceDataType method to convert the data
        to the correct type.

        The purpose of the defaultData is to reset a config data to its initial value when the
        user clicks on the reset button during editing. The getNonDefaultsDict returns a dictionary
        containing only the items that differ from their default values. This is used to store the
        persistent settings between runs. When a developer changes the default value in a future
        version, the new value will be updated in the UI unless the user has explicitly changed the
        value himself.
    """
    def __init__(self, nodeName, defaultData, enabled=True, expanded=True):
        """ Constructor
            :param nodeName: name of this node (used to construct the node path).
            :param data: the configuration data. If omitted the defaultData will be used.
            :param defaultData: default data to which the data can be reset by the reset button.
            :param enabled: True if the item is enabled
            :param expanded: True if the item is expanded
        """
        super(AbstractCti, self).__init__(nodeName=nodeName)

        self._defaultData = self._enforceDataType(defaultData)
        self._data = self.defaultData
        self._enabled = enabled
        self._expanded = expanded
        self._blockRefresh = False


    def finalize(self):
        """ Can be used to cleanup resources. Should be called explicitly.
            Recursively calls the _closeRecources method on all children and then on itself.
            Descendants should override _closeRecources to do the actual closing of resources.
        """
        for child in self.childItems:
            child.finalize()

        # In contrast to the BaseRti there is no close() method, _closeResources is directly called
        # because it only is needed when the config is deleted and catching exceptions makes no
        # sense.
        self._closeResources()


    def _closeResources(self):
        """ Can be overridden to close the underlying resources or disconnect signals.
            The default implementation does nothing.
            Is called by self.finalize when the cti is deleted. There is no corresponding
            _openResources; all resources are claimed in the constructor.
        """
        pass


    def __eq__(self, other):
        """ Returns true if self == other.
        """
        result = (type(self) == type(other) and
                  self.nodeName == other.nodeName and
                  self.data == other.data and
                  self.defaultData == other.defaultData and
                  self.childItems == other.childItems)
        return result

    def __ne__(self, other):
        """ Returns true if self != other.
        """
        return not self.__eq__(other)

    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return ""


    def _dataToString(self, data):
        """ Conversion function used to convert the (default)data to the display value.
        """
        return str(data)

    @property
    def displayValue(self):
        """ Returns the string representation of data for use in the tree view.
            If a descendant overrides this, it should probably also override displayDefaultValue.
        """
        return self._dataToString(self.data)

    @property
    def displayDefaultValue(self):
        """ Returns the string representation of default data for use in the tree view.
        """
        return self._dataToString(self.defaultData)

    @property
    def configValue(self):
        """ Returns the configuration value of this item.
            By default this is the same as the underlying data but it can be overridden,
        """
        return self.data

    @property
    def data(self):
        """ Returns the data of this item.
        """
        return self._data

    @data.setter
    def data(self, data):
        """ Sets the data of this item.
            Does type conversion to ensure data is always of the correct type.
        """
        # Descendants should convert the data to the desired type here
        self._data = self._enforceDataType(data)

    @property
    def defaultData(self):
        """ Returns the default data of this item.
        """
        return self._defaultData

    @defaultData.setter
    def defaultData(self, defaultData):
        """ Sets the data of this item.
            Does type conversion to ensure default data is always of the correct type.
        """
        # Descendants should convert the data to the desired type here
        self._defaultData = self._enforceDataType(defaultData)

    def _enforceDataType(self, value):
        """ Converts data to the type of this CTI.
            Used by the setter to ensure that the data and defaultData have the correct type
        """
        raise NotImplementedError()

    @property
    def checkState(self):
        """ Returns how the checkbox for this cti should look like. Returns None for no checkbox.
            :rtype: Qt.CheckState or None
        """
        return None

    @checkState.setter
    def checkState(self, checkState):
        """ Allows the data to be set given a Qt.CheckState.
            Abstract method; you must override it if valueColumnItemFlags returns
            Qt.ItemIsUserCheckable
        """
        raise NotImplementedError()

    @property
    def enabled(self):
        """ Returns the enabled flag which determines if the user can interact with this item.
        """
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        """ Sets the enabled flag which determines if the user can interact with this item.
        """
        #logger.debug("Setting enabled = {:5} for {}".format(enabled, self))
        self._enabled = enabled


    @property
    def expanded(self):
        """ Returns the expanded flag which keeps
        """
        return self._expanded

    @expanded.setter
    def expanded(self, expanded):
        """ Keeps track if the config item is expanded.
            Needed to keep state between changing inspectors.
            Note, this can only be used as an initial expanded value but does not update the tree
            when it's constructed. Use ConfigTree.expand for that.
        """
        #logger.debug("Setting expanded = {!r:5} for {}".format(expanded, self))
        self._expanded = expanded


    def enableBranch(self, enabled):
        """ Sets the enabled member to True or False for a node and all it's children
        """
        self.enabled = enabled
        for child in self.childItems:
            child.enableBranch(enabled)


    def resetToDefault(self, resetChildren=True):
        """ Resets the data to the default data. By default the children will be reset as well
        """
        self.data = self.defaultData
        if resetChildren:
            for child in self.childItems:
                child.resetToDefault(resetChildren=True)


    def getRefreshBlocked(self):
        """ If True the calls to _refreshNodeFromTarget are blocked.
            This calls self.model.getRefreshBlocked(), so this value is always equal for all
            config tree items in the model
        """
        return self.model.getRefreshBlocked()


    def refreshFromTarget(self, level=0):
        """ Refreshes the configuration tree from the target it monitors (if present).
            Recursively call _refreshNodeFromTarget for itself and all children. Subclasses should
            typically override _refreshNodeFromTarget instead of this function.
            During updateTarget's execution refreshFromTarget is blocked to avoid loops.
        """
        if self.getRefreshBlocked():
            logger.debug("_refreshNodeFromTarget blocked")
            return

        if False and level == 0:
            logger.debug("refreshFromTarget: {}".format(self.nodePath))

        self._refreshNodeFromTarget()
        for child in self.childItems:
            child.refreshFromTarget(level=level + 1)


    def _refreshNodeFromTarget(self):
        """ Refreshes the configuration from the target it monitors (if present).
            The default implementation does nothing; subclasses can override it.
            During updateTarget's execution refreshFromTarget is blocked to avoid loops.
            Typically called from inspector.drawTarget
        """
        pass


    def updateTarget(self, level=0):
        """ Applies the configuration to the target it monitors (if present).
            Recursively call _updateTargetFromNode for itself and all children. Subclasses should
            typically override _updateTargetFromNode instead of this function.

            :param level: the level of recursion.
        """
        #if level == 0:
        #    logger.debug("updateTarget: {}".format(self.nodePath))

        self._updateTargetFromNode()
        for child in self.childItems:
            child.updateTarget(level = level + 1)


    def _updateTargetFromNode(self):
        """ Applies the configuration to the target it monitors (if present).
            The default implementation does nothing; subclasses can override it.
            During updateTarget's execution refreshFromTarget is blocked to avoid loops.
        """
        pass



    #################
    # serialization #
    #################

    @classmethod
    def __not_used__createFromJsonDict(cls, dct):
        """ Creates a CTI given a dictionary, which usually comes from a JSON decoder.
        """
        cti = cls(dct['nodeName'])
        if 'data' in dct:
            cti.data = dct['data']
        if 'defaultData' in dct:
            cti.defaultData = dct['defaultData']

        for childCti in dct['childItems']:
            cti.insertChild(childCti)

        if '_class_' in dct: # sanity check
            assert get_full_class_name(cti) == dct['_class_'], \
                "_class_ should be: {}, got: {}".format(get_full_class_name(cti), dct['_class_'])
        return cti


    def __not_used__asJsonDict(self):
        """ Returns a dictionary representation to be used in a JSON encoder,
        """
        return {'_class_': get_full_class_name(self),
                'nodeName': self.nodeName,
                'data': self._dataToJson(self.data),
                'defaultData': self._dataToJson(self.defaultData),
                'childItems': self.childItems}


    def _nodeGetNonDefaultsDict(self):
        """ Retrieves this nodes` values as a dictionary to be used for persistence.
            A dictionary with the data value will be returned if the data is not equal to the
            defaultData, the node is enabled and the node is editable. Otherwise and empty
            dictionary is returned.

            Non-recursive auxiliary function for getNonDefaultsDict
        """
        dct = {}
        isEditable = bool(int(self.valueColumnItemFlags) and Qt.ItemIsEditable)
        if (self.data != self.defaultData and self.enabled and isEditable):
            dct['data'] = self.data
        return dct


    # TODO: think of smaller format. E.g. {'name1': val, 'n2', v2, _children = {...}}
    # Or just {'node/path/name1': value, ...}
    def getNonDefaultsDict(self):
        """ Recursively retrieves values as a dictionary to be used for persistence.
            Does not save defaultData and other properties, only stores values if they differ from
            the defaultData. If the CTI and none of its children differ from their default, a
            completely empty dictionary is returned. This is to achieve a smaller json
            representation.

            Typically descendants should override _nodeGetNonDefaultsDict instead of this function.
        """
        dct = self._nodeGetNonDefaultsDict()

        childList = []
        for childCti in self.childItems:
            childDct = childCti.getNonDefaultsDict()
            if childDct:
                childList.append(childDct)
        if childList:
            dct['childItems'] = childList

        if dct:
            dct['nodeName'] = self.nodeName

        return dct


    def _nodeSetValuesFromDict(self, dct):
        """ Sets values from a dictionary in the current node.
            Non-recursive auxiliary function for setValuesFromDict
        """
        if 'data' in dct:
            self.data = dct['data']

    def setValuesFromDict(self, dct):
        """ Recursively sets values from a dictionary created by getNonDefaultsDict.

            Does not raise exceptions (logs warnings instead) so that we can remove/rename node
            names in future Argos versions (or remove them) without breaking the application.

            Typically descendants should override _nodeSetValuesFromDict instead of this function.
        """
        if 'nodeName' not in dct:
            return

        nodeName = dct['nodeName']
        if nodeName != self.nodeName:
            msg = "nodeName mismatch: expected {!r}, got {!r}".format(self.nodeName, nodeName)
            if DEBUGGING:
                raise ValueError(msg)
            else:
                logger.warn(msg)
                return

        self._nodeSetValuesFromDict(dct)

        for childDct in dct.get('childItems', []):
            key = childDct['nodeName']
            try:
                childCti = self.childByNodeName(key)
            except IndexError as _ex:
                logger.warn("Unable to set values for: {}".format(key))
            else:
                childCti.setValuesFromDict(childDct)

    ########################
    # Editor look and feel #
    ########################

    @property
    def valueColumnItemFlags(self):
        """ Returns Qt.ItemFlag enum that will be used for the value column in the config tree.
            These flags determine how the user can interact with the value column (e.g. can edit).

            Note that the ConfigTreeModel may override them: it will add the Qt.ItemIsEnabled and
            Qt.ItemIsSelectable to the flags.

            The base implementation of valueColumnItemFlags returns Qt.ItemIsEditable. Make sure to
            implement the createEditor abstract method if Qt.ItemIsEditable is included in the
            result.
        """
        return Qt.ItemIsEditable


    def createEditor(self, delegate, parent, option):
        """ Creates an editor (QWidget) for editing.
            It's parent will be set by the ConfigItemDelegate class that calls this method.

            :param delegate: the delegate that called this function
            :type  delegate: ConfigItemDelegate
            :param parent: The parent widget for the editor
            :type  parent: QWidget
            :param option: describes the parameters used to draw an item in a view widget.
            :type  option: QStyleOptionViewItem
        """
        raise NotImplementedError("createEditor not implemented while Qt.ItemIsEditable is set")



class AbstractCtiEditor(QtWidgets.QWidget):
    """ An editor for use in the ConfigTreeView (CTI).

        It consists of a horizontal collection of child widgets, the last of which is a reset
        button which will reset the config data to its default when clicked.

        You must implemented setData and getData, which pass the data from the
        QConfigItemDelegate to the editor and back.
    """
    def __init__(self, cti, delegate, subEditors=None, parent=None):
        """ Wraps the child widgets in a horizontal layout and appends a reset button.

            Maintains a reference to the ConfigTreeItem (cti) and to delegate, this last reference
            is so that we can command the delegate to commit and close the editor.

            The subEditors must be a list of QWidgets. Note that the sub editors do not yet have
            to be initialized with editor data since setData will be called by the delegate
            after construction. There it can be taken care of.
        """
        super(AbstractCtiEditor, self).__init__(parent=parent)

        # Prevent underlying table cell from being visible if the editor doesn't fill the cell
        self.setAutoFillBackground(True)

        self._subEditors = []
        self.delegate = delegate
        self.cti = cti

        # From the QAbstractItemDelegate.createEditor docs: The returned editor widget should have
        # Qt.StrongFocus; otherwise, QMouseEvents received by the widget will propagate to the view.
        # The view's background will shine through unless the editor paints its own background
        # (e.g., with setAutoFillBackground()).
        self.setFocusPolicy(Qt.StrongFocus)

        self.hBoxLayout = QtWidgets.QHBoxLayout()
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSpacing(0)
        self.setLayout(self.hBoxLayout)

        self.resetButton = QtWidgets.QToolButton()
        self.resetButton.setText("Reset")
        self.resetButton.setToolTip("Reset to default value.")
        self.resetButton.setIcon(QtGui.QIcon(os.path.join(icons_directory(), 'reset-l.svg')))
        self.resetButton.setFocusPolicy(Qt.NoFocus)
        self.resetButton.clicked.connect(self.resetEditorValue)
        self.hBoxLayout.addWidget(self.resetButton, alignment=Qt.AlignRight)

        self.cti.model.sigItemChanged.connect(self.modelItemChanged)

        for subEditor in (subEditors if subEditors is not None else []):
            self.addSubEditor(subEditor)


    def finalize(self):
        """ Called at clean up, when the editor is closed. Can be used to disconnect signals.
            This is often called after the client (e.g. the inspector) is updated. If you want to
            take action before the update, override prepareCommit instead.
            Be sure to call the finalize of the super class if you override this function.
        """
        for subEditor in self._subEditors:
            self.removeSubEditor(subEditor)

        self.cti.model.sigItemChanged.disconnect(self.modelItemChanged)
        self.resetButton.clicked.disconnect(self.resetEditorValue)
        self.cti = None # just to make sure it's not used again.
        self.delegate = None


    @QtSlot()
    def prepareCommit(self):
        """ Called just before the data is committed.
            Can be used to take action before the client (e.g. the inspector) is updated.
        """
        logger.debug("Committing data from: {}".format(self.cti.nodePath))


    def addSubEditor(self, subEditor, isFocusProxy=False):
        """ Adds a sub editor to the layout (at the right but before the reset button)
            Will add the necessary event filter to handle tabs and sets the strong focus so
            that events will not propagate to the tree view.

            If isFocusProxy is True the sub editor will be the focus proxy of the CTI.
        """
        self.hBoxLayout.insertWidget(len(self._subEditors), subEditor)
        self._subEditors.append(subEditor)

        subEditor.installEventFilter(self)
        subEditor.setFocusPolicy(Qt.StrongFocus)

        if isFocusProxy:
            self.setFocusProxy(subEditor)

        return subEditor


    def removeSubEditor(self, subEditor):
        """ Removes the subEditor from the layout and removes the event filter.
        """
        if subEditor is self.focusProxy():
            self.setFocusProxy(None)

        subEditor.removeEventFilter(self)
        self._subEditors.remove(subEditor)
        self.hBoxLayout.removeWidget(subEditor)


    def setData(self, value):
        """ Provides the editor widget with a data to manipulate.
            Value originates from the ConfigTreeModel.data(role=QEditRole).
        """
        raise NotImplementedError()


    def getData(self):
        """ Gets data from the editor widget.
            Should return a value that can be set into the ConfigTreeModel with the QEditRole.
        """
        raise NotImplementedError()


    def eventFilter(self, watchedObject, event):
        """ Calls commitAndClose when the tab and back-tab are pressed.
            This is necessary because, normally the event filter of QStyledItemDelegate does this
            for us. However, that event filter works on this object, not on the sub editor.
        """
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if key in (Qt.Key_Tab, Qt.Key_Backtab):
                self.commitAndClose()
                return True
            else:
                return False

        return super(AbstractCtiEditor, self).eventFilter(watchedObject, event)


    @QtSlot(BaseTreeItem)
    def modelItemChanged(self, cti):
        """ Called when the an Config Tree Item (CTI) in the model has changed.

            If the CTI is a different one than the CTI that belongs to this editor, the editor
            is closed. This can happen if the user has checked a checkbox. Qt does not close other
            editors in the view in that case, so this is why we do it here.

            If the cti parameter is the CTI belonging to this editor, nothing is done. We don't
            close the editor because the user may want to continue editing.
        """
        if cti is not self.cti:
            logger.debug("Another config tree item has changed: {}. Closing editor for {}"
                         .format(cti, self.cti))
            self.delegate.closeEditor.emit(self, QtWidgets.QAbstractItemDelegate.NoHint) # CLOSES SELF!
        else:
            logger.debug("Cti of this editor has changed: {}".format(cti))


    @QtSlot()
    def commitAndClose(self):
        """ Commits the data of the sub editor and instructs the delegate to close this ctiEditor.

            The delegate will emit the closeEditor signal which is connected to the closeEditor
            method of the ConfigTreeView class. This, in turn will, call the finalize method of
            this object so that signals can be disconnected and resources can be freed. This is
            complicated but I don't see a simpler solution.
        """
        if self.delegate:
            self.delegate.commitData.emit(self)
            self.delegate.closeEditor.emit(self, QtWidgets.QAbstractItemDelegate.NoHint) # CLOSES SELF!
        else:
            # QAbstractItemView.closeEditor is sometimes called directly, without the
            # QAbstractItemDelegate.closeEditor signal begin emitted, e.g when the currentItem
            # changes. Therefore the commitAndClose method can be called twice, if we call it
            # explicitly as well (e.g. in FontCtiEditor.execFontDialog(). We guard against this.
            logger.debug("AbstractCtiEditor.commitAndClose: editor already closed (ignored).")


    @QtSlot(bool)
    def resetEditorValue(self, checked=False):
        """ Resets the editor to the default value. Also resets the children.
        """
        # Block all signals to prevent duplicate inspector updates.
        # No need to restore, the editors will be deleted after the reset.
        for subEditor in self._subEditors:
            subEditor.blockSignals(True)

        self.cti.resetToDefault(resetChildren=True)
        # This will commit the children as well.
        self.setData(self.cti.defaultData)
        self.commitAndClose()


    def paintEvent(self, event):
        """ Reimplementation of paintEvent to allow for style sheets
            See: http://qt-project.org/wiki/How_to_Change_the_Background_Color_of_QWidget
        """
        opt = QtWidgets.QStyleOption()
        opt.initFrom(self)
        painter = QtGui.QPainter(self)
        self.style().drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, painter, self)
        painter.end()

