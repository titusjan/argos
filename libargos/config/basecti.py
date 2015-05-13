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

""" Configuration TreeItem (CTI) classes
    Tree items for use in the ConfigTreeModel
"""
import logging, os
from json import JSONEncoder, JSONDecoder, dumps

from libargos.info import DEBUGGING, icons_directory
from libargos.qt import Qt, QtCore, QtGui, QtSlot
from libargos.qt.treeitems import BaseTreeItem
from libargos.utils.cls import get_full_class_name, import_symbol
from libargos.utils.misc import NOT_SPECIFIED


logger = logging.getLogger(__name__)


class InvalidInputError(Exception):
    """ Exception raised when the input is invalid after editing
    """
    pass



class CtiEditor(QtGui.QWidget):
    """ An editor for use in the ConfigTreeView.
    
        It is a horizontal collection of child widgets, the last of which is a reset button.
        The reset button will reset the config data to its default.
        
        The first editor is considered the main editor. This editor will receive the focus.
    """
    def __init__(self, cti, delegate, *childWidgets, parent=None):
        """ Wraps the child widgets in a horizontal layout and appends a reset button.
            
            Maintains a reference to the ConfigTreeItem (cti) and to delegate, this last reference
            is so that we can command the delegate to commit and close the editor.
        """
        super(CtiEditor, self).__init__(parent=parent)

        assert parent, "parent undefined"
        assert len(childWidgets) >= 1, "You should specify at least one childWidget"

        self.delegate = delegate
        self.cti = cti
        
        hBoxLayout = QtGui.QHBoxLayout()
        hBoxLayout.setContentsMargins(0, 0, 0, 0)
        hBoxLayout.setSpacing(0)
        self.setLayout(hBoxLayout)

        self.childWidgets = childWidgets
        for childWidget in childWidgets:
            hBoxLayout.addWidget(childWidget)

        self.button = QtGui.QToolButton() # TODO: rename to resetButton
        self.button.setText("Reset")
        self.button.setIcon(QtGui.QIcon(os.path.join(icons_directory(), 'err.warning.svg')))
        self.button.setFocusPolicy(Qt.NoFocus)
        self.button.clicked.connect(self.resetEditorValue)
        hBoxLayout.addWidget(self.button)
        
        # From the QAbstractItemDelegate.createEditor docs: The returned editor widget should have 
        # Qt.StrongFocus; otherwise, QMouseEvents received by the widget will propagate to the view. 
        # The view's background will shine through unless the editor paints its own background 
        # (e.g., with setAutoFillBackground()).
        #self.setFocusPolicy(Qt.NoFocus)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(self.mainEditor)
        self.mainEditor.setFocusPolicy(Qt.NoFocus)
        
        self.mainEditor.installEventFilter(self)
        

    def eventFilter(self, watchedObject, event):
        """ Calls commitAndClose when the tab and back-tab are pressed.
            This is necessary because, normally the event filter of QStyledItemDelegate does this
            for us. However, that event filter works on this object, not on the main editor.
        """
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if key in (Qt.Key_Tab, Qt.Key_Backtab):
                self.commitAndClose()
                return True
            else:
                return False

        return super(CtiEditor, self).eventFilter(watchedObject, event) 
            
        
#    def event(self, event):
#        #if not isinstance(event, QtGui.QPaintEvent):
#        if isinstance(event, (QtGui.QFocusEvent)):
#            logger.debug("CtiEditor.event: {!r} (type={})".format(event, event.type()))
#        return super(CtiEditor, self).event(event)
#    
#        
#    def keyPressEvent(self, event):
#        #if not isinstance(event, QtGui.QPaintEvent):
#        if isinstance(event, (QtGui.QKeyEvent, QtGui.QFocusEvent)):
#            logger.debug("CtiEditor.keyEvent: {!r} (type={}), (key={})".format(event, event.type(), event.key()))
#        return super(CtiEditor, self).keyPressEvent(event)

    
    def finalize(self):
        """ Called at clean up. Can be used to disconnect signals.
        """
        logger.debug("CtiEditor.finalize")
        self.mainEditor.removeEventFilter(self)
        self.cti.finalizeEditor(self, self.delegate)
        self.cti = None # just to make sure it's not used again.
        self.button.clicked.disconnect(self.resetEditorValue)

        
    @property
    def mainEditor(self):
        """ Returns the first child widget 
        """
        return self.childWidgets[0]
    
    
    @QtSlot()
    def commitAndClose(self):
        """ Commits the data of the main editor and instructs the delegate to close this ctiEditor.
        
            The delegate will emit the closeEditor signal which is connected to the closeEditor
            method of the ConfigTreeView class. This, in turn will, call the finalize method of
            this object so that signals can be disconnected and resources can be freed. This is
            complicated but I don't see a simpler solution.
        """
        logger.debug("CtiEditor.commitAndClose... committing")
        self.delegate.commitData.emit(self)
        logger.debug("CtiEditor.commitAndClose... closing")
        self.delegate.closeEditor.emit(self, QtGui.QAbstractItemDelegate.NoHint)   # CLOSES SELF!
        

    @QtSlot(bool)
    def resetEditorValue(self, checked=False):
        """ Resets the main editor to the default value of the config tree item
        """
        logger.debug("resetEditorValue: {}".format(checked))
        self.cti.setEditorValue(self, self.cti.defaultData)
        self.commitAndClose()
    
    
    def paintEvent(self, event):
        """ Reimplementation of paintEvent to allow for style sheets
            See: http://qt-project.org/wiki/How_to_Change_the_Background_Color_of_QWidget
        """
        opt = QtGui.QStyleOption()
        opt.initFrom(self)
        painter = QtGui.QPainter(self)
        self.style().drawPrimitive(QtGui.QStyle.PE_Widget, opt, painter, self)
        painter.end()



class BaseCti(BaseTreeItem):
    """ TreeItem for use in a ConfigTreeModel. (CTI = Config Tree Item)

        Base node from which to derive the other types of nodes.
        Serves as an interface but can also be instantiated for debugging purposes.
        
        Just like the BaseTreeItem every node has a name and a full path that is a slash-separated 
        string of the full path leading from the root node to the current node. For instance, the 
        path may be '/scale/x', the nodeName in that case is 'x'. 
        
        CTIs are used to store a certain configuration value. It can be queried by the configValue
        property. The type of this value differs between descendants of BaseCti, but a sub class
        should always return the same type. For example, the ColorCti.configValue always returns a
        QColor object. The displayValue returns the string representation for use in the tables; 
        by default this returns: str(configValue)
        
        The underlying data is usually stored in that type as well but this is not necessarily so.
        A ChoiceCti, which represents a combo box, stores a list of choices and an index that is
        actual choice made by the user. ChoiceCti.data contains the index while ChoiceCti.configData
        returns: choices[index]. Note that the constructor expects the data as input parameter. The
        constructor calls the _enforceDataType method to convert the data to the correct type.
        
        The purpose of the defaultData is to reset a config data to its initial value when the 
        user clicks on the reset button during editing. The getNonDefaultsDict returns a dictionary 
        containing only the items that differ from their default values. This is used to store the 
        persistent settings between runs. When a developer changes the default value in a future
        version, the new value will be updated in the UI unless the user has explicitly set the
        value himself.
        
        Each CTI can be edited. The createEditor must be overridden so that it creates the
        desired editor (a QWidget) when the user starts editing. The setEditorValue sets the
        editor widget's value from the CTI data. The getEditorData does the inverse when the user
        has finished editing. These methods are all called by the ConfigItemDelegate class. You
        can read more about delegates in the model/view programming page of the QT documentation: 
        http://doc.qt.io/qt-4.8/model-view-programming.html
    """
    def __init__(self, nodeName, data=NOT_SPECIFIED, defaultData=None):
        """ Constructor
            :param nodeName: name of this node (used to construct the node path).
            :param data: the configuration data. If omitted the defaultData will be used.
            :param defaultData: default data to which the data can be reset or initialized if 
                omitted from the constructor.
        """
        super(BaseCti, self).__init__(nodeName=nodeName)

        self._defaultData = self._enforceDataType(defaultData)

        if data is NOT_SPECIFIED:
            self._data = self.defaultData
        else:
            self._data = self._enforceDataType(data)
         
    
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
    
    @property
    def displayValue(self):
        """ Returns the string representation of data for use in the tree view. 
        """
        return str(self.value)
    
    @property
    def value(self):
        """ Returns the configuration value of this item. 
            By default this is the same as the underlying data but it can be overridden, 
            e.g. when the data is an index in a combo box and the value returns the choice.
        """
        return self._data
    
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
            The default implementation does nothing; should be overridden by descendants.
        """
        return value
    
   
    @property
    def checkState(self):
        """ Returns how the checkbox for this cti should look like. Returns None for no checkbox. 
            :rtype: Qt.CheckState or None 
        """
        return None

    @checkState.setter
    def checkState(self, checkState):
        """ Allows the data to be set given a Qt.CheckState.
            Is an abstract method. Can be overridden.
        """
        raise NotImplementedError()

   
    @property
    def valueColumnItemFlags(self):
        """ Returns Qt.ItemFlag enum that will be used for the value column in the config tree.
            These flags determine how the user can interact with the value column (e.g. can edit).
            
            Note that the ConfigTreeModel may override them: the current implementation will add
            the Qt.ItemIsEnabled and Qt.ItemIsSelectable to the flags. 
        """
        return Qt.ItemIsEditable 

    #### The following methods are called by the ConfigItemDelegate class ####
    
    
    
    def createEditor(self, delegate, parent, option):
        """ Creates an editor (QWidget) for editing. 
            It's parent will be set by the ConfigItemDelegate class
            :param delegate: the delegate that called this function
            :type  delegate: ConfigItemDelegate
            :param parent: The parent widget for the editor
            :type  parent: QWidget
            :param option: describes the parameters used to draw an item in a view widget.
            :type  option: QStyleOptionViewItem
        """
        lineEditor = QtGui.QLineEdit()
        ctiEditor = CtiEditor(self, delegate, lineEditor, parent=parent) 
        #editor.setText(str(self.data)) # not necessary, it will be done by setEditorValue
        return ctiEditor
        
    
    def finalizeEditor(self, ctiEditor, delegate):
        """ Is called when the editor is closed. 
            Can be used for disconnecting slots and to free resources.
        """
        pass

        
    def setEditorValue(self, ctiEditor, value):
        """ Provides the editor widget with a data to manipulate.
            
            The data parameter could be replaced by self.data but the caller 
            (ConfigItemelegate.getModelData) retrieves it via the model to be consistent 
            with setModelData.
             
            :type editor: QWidget
        """
        lineEditor = ctiEditor.mainEditor
        lineEditor.setText(str(value))
        
        
    def getEditorValue(self, ctiEditor):
        """ Gets data from the editor widget.
            
            :type editor: QWidget
        """
        lineEditor = ctiEditor.mainEditor
        return lineEditor.text()


    def paintDisplayValue(self, painter, option, value):
        """ Can be overridden to paint a widget in display mode.
            Should return True, otherwise the displayValue property is written in the cell.
            The default implementation returns False.
        """
        return False
    
    
    #### The following methods are for (de)serialization ####
    

    @classmethod        
    def createFromJsonDict(cls, dct):
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


    def _dataToJson(self, data):
        """ Converts data or defaultData to serializable json dictionary or scalar.
            Helper function that can be overridden; by default the input is returned.
        """
        return data
    
    
    def _dataFromJson(self, json):
        """ Converts json dictionary or scalar to an object to use in self.data or defaultData.
            Helper function that can be overridden; by default the input is returned.
        """
        return json
    

    def asJsonDict(self):
        """ Returns a dictionary representation to be used in a JSON encoder,
        """
        return {'_class_': get_full_class_name(self),
                'nodeName': self.nodeName, 
                'data': self._dataToJson(self.data), 
                'defaultData': self._dataToJson(self.defaultData), 
                'childItems': self.childItems}
        

    def getNonDefaultsDict(self):
        """ Recursively retrieves values as a dictionary to be used for persistence.
            Does not save defaultData and other properties.
            Only stores values if they differ from the defaultData. If the CTI and none of its 
            children differ from their default, a completely empty dictionary is returned. 
            This is to achieve a smaller json representation.
        """
        dct = {}
        if self.data != self.defaultData:
            dct['data'] = self._dataToJson(self.data)
            
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
                

    def setValuesFromDict(self, dct):
        """ Recursively sets values from a dictionary created by getNonDefaultsDict.
         
            Does not raise exceptions (only logs warnings) so that we can remove/rename node
            names in new Argos versions (or remove them) without breaking the application.
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
            
        if 'data' in dct:
            self.data = self._dataFromJson(dct['data'])
        
        for childDct in dct.get('childItems', []):
            key = childDct['nodeName']
            try:
                childCti = self.childByNodeName(key)
            except IndexError as _ex:
                logger.warn("Unable to set values for: {}".format(key))
                
            childCti.setValuesFromDict(childDct)
    

                

#################
# JSON encoding #    
#################

def ctiDumps(obj, sort_keys=True, indent=4):
    """ Dumps cti as JSON string """
    return dumps(obj, sort_keys=sort_keys, cls=CtiEncoder, indent=indent)


class CtiEncoder(JSONEncoder):
    """ JSON encoder that knows how to encode BaseCti objects
    """
    def default(self, obj):
        if isinstance(obj, BaseCti):
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


        
