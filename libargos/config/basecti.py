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

from libargos.info import DEBUGGING
from libargos.qt import QtGui
from libargos.qt.treeitems import BaseTreeItem
from libargos.utils.cls import get_full_class_name, import_symbol
from libargos.utils.misc import NOT_SPECIFIED


logger = logging.getLogger(__name__)



class BaseCti(BaseTreeItem):
    """ TreeItem for use in a ConfigTreeModel. (RTI = Config TreeItem)
        Base node from which to derive the other types of nodes.

        Serves as an interface but can also be instantiated for debugging purposes.
    """
    def __init__(self, nodeName, value=NOT_SPECIFIED, defaultValue=None):
        """ Constructor
            :param nodeName: name of this node (used to construct the node path).
            :param value: the configuration value. If omitted the defaultValue will be used.
            :param defaultValue: default value to which the value can be reset or initialized
                if omitted  from the constructor
        """
        super(BaseCti, self).__init__(nodeName=nodeName)

        self._defaultValue = self._convertValueType(defaultValue)

        if value is NOT_SPECIFIED:
            self._value = self.defaultValue
        else:
            self._value = self._convertValueType(value)
         
    
    def __eq__(self, other): 
        """ Returns true if self == other. 
        """
        result = (type(self) == type(other) and 
                  self.nodeName == other.nodeName and
                  self.value == other.value and
                  self.defaultValue == other.defaultValue and
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
        """ Returns the string representation of value for use in the tree view. 
        """
        return str(self._value)
    
    @property
    def value(self):
        """ Returns the value of this item. 
        """
        return self._value

    @value.setter
    def value(self, value):
        """ Sets the value of this item. 
            Does type conversion to ensure value is always of the correct type.
        """
        # Descendants should convert the value to the desired type here
        self._value = self._convertValueType(value)
            
    @property
    def defaultValue(self):
        """ Returns the default value of this item. 
        """
        return self._defaultValue

    @defaultValue.setter
    def defaultValue(self, defVal):
        """ Sets the value of this item. 
            Does type conversion to ensure default value is always of the correct type.
        """
        # Descendants should convert the value to the desired type here
        self._defaultValue = self._convertValueType(defVal)
        
    
    def _convertValueType(self, value):
        """ Converts value to the type of this CTI.
            Used by the setter to ensure that the value and defaultValue have the correct type 
            The default implementation does nothing; should be overridden by descendants.
        """
        return value
    

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
        editor = QtGui.QLineEdit(parent)
        #editor.setText(str(self.value)) # not necessary, it will be done by setEditorValue
        return editor
        
        
    def setEditorValue(self, editor, value):
        """ Provides the editor widget with a value to manipulate.
            
            The value parameter could be replaced by self.value but the caller 
            (ConfigItemelegate.getModelData) retrieves it via the model to be consistent 
            with setModelData.
             
            :type editor: QWidget
        """
        lineEditor = editor
        lineEditor.setText(str(value))
        
        
    def getEditorValue(self, editor):
        """ Gets data from the editor widget.
            
            :type editor: QWidget
        """
        lineEditor = editor
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
        if 'value' in dct:
            cti.value = dct['value']
        if 'defaultValue' in dct:
            cti.defaultValue = dct['defaultValue']
            
        for childCti in dct['childItems']:
            cti.insertChild(childCti)
            
        if '_class_' in dct: # sanity check
            assert get_full_class_name(cti) == dct['_class_'], \
                "_class_ should be: {}, got: {}".format(get_full_class_name(cti), dct['_class_'])             
        return cti


    def asJsonDict(self):
        """ Returns a dictionary representation to be used in a JSON encoder,
        """
        return {'_class_': get_full_class_name(self),
                'nodeName': self.nodeName, 'value': self.value, 
                'defaultValue': self.defaultValue, 'childItems': self.childItems}
        

    def getNonDefaultsDict(self):
        """ Recursively retrieves values as a dictionary to be used for persistence.
            Does not save defaultValue and other properties.
            Only stores values if they differ from the defaultValue. If the CTI and none of its 
            children differ from their default, a completely empty dictionary is returned. 
            This is to achieve a smaller json representation.
        """
        dct = {}
        if self.value != self.defaultValue:
            dct['value'] = self.value
            
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
            
        if 'value' in dct:
            self.value = dct['value']
        
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
    """ Config tree item JSON decoding function.
        Returns a CTI given a dictionary of attributes.
        The full class name of desired CTI class should be in dct['_class_''].
    """
    if '_class_'in dct:
        full_class_name = dct['_class_'] # TODO: how to handle the full_class_name?
        cls = import_symbol(full_class_name)
        return cls.createFromJsonDict(dct)
    else:
        return dct

    
class CtiDecoder(JSONDecoder):
    """ Config tree item JSON decoder class. Not strictly necessary, you can use the
        jsonAsCti function as object_hook directly in loads, but since we also have an 
        encoder class it feels right to have a decoder as well.
    """
    def __init__(self, *args, **kwargs):
        # The object_hook must be given to the parent constructor since that makes 
        # an internal scanner.
        super(CtiDecoder, self).__init__(*args, object_hook = jsonAsCti, **kwargs)


        
