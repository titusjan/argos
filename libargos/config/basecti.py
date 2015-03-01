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

""" Repository TreeItem (RTI) classes
    Tree items for use in the RepositoryTreeModel
"""
import logging, os, json
from json import JSONEncoder, JSONDecoder

from libargos.info import program_directory, DEBUGGING
from libargos.qt import QtGui 
from libargos.qt.treeitems import BaseTreeItem
from libargos.utils.cls import get_full_class_name, import_symbol

ICONS_DIRECTORY = os.path.join(program_directory(), 'img/icons')

logger = logging.getLogger(__name__)


class BaseCti(BaseTreeItem):
    """ TreeItem for use in a ConfigTreeModel. (RTI = Config TreeItem)
        Base node from which to derive the other types of nodes.

        Serves as an interface but can also be instantiated for debugging purposes.
    """
    def __init__(self, nodeName='', value=None, defaultValue=None): # TODO: mandatory (default)value?
        """ Constructor
        
            :param nodeName: name of this node (used to construct the node path).
            :param fileName: absolute path to the file where the data of this RTI originates.
        """
        super(BaseCti, self).__init__(nodeName=nodeName)

        self._value = value
        self._defaultValue = defaultValue
        
    
    def __eq__(self, other): 
        return (type(self) == type(other) and 
                self.nodeName == other.nodeName and
                self.value == other.value and
                self.defaultValue == other.defaultValue)

    @classmethod        
    def createFromJsonDict(cls, dct):
        """ Creates a CTI given a dictionary, which usually comes from a JSON decoder.
        """
        cti = cls(dct['nodeName'], value=dct['value'])
        if 'defaultValue' in dct:
            cti._defaultValue = dct['defaultValue']
            
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

    
    @property
    def value(self):
        """ Returns the value of this item. 
        """
        return self._value

    @value.setter
    def value(self, value):
        """ Sets the value of this item. 
        """
        self._value = value
            
    @property
    def defaultValue(self):
        """ Returns the default value of this item. 
        """
        return self._defaultValue
            
    @property
    def type(self):
        """ Returns type of the value of this item. 
        """
        return '<to be implemented?'
        #return self._type
    
    
class CtiEncoder(JSONEncoder):
    
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
        encoder class it feels right to have a decorer as well.
    """
    def __init__(self, *args, **kwargs):
        # The object_hook must be given to the parent constructor since that makes 
        # an internal scanner.
        super(CtiDecoder, self).__init__(*args, object_hook = jsonAsCti, **kwargs)

        
if __name__ == "__main__":
    import sys
    logging.basicConfig(level='DEBUG', stream=sys.stderr,
                        format='%(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-7s: %(message)s')    
    
    def mydumps(obj):
        return json.dumps(obj, sort_keys=True, cls=CtiEncoder, indent=4)
    
    
    def main1():
        rootItem = BaseCti(nodeName='<invisible-root>', value=0.123456789012345678901234567890)
        rootItem.insertChild(BaseCti(nodeName='kinders', value=-7))
        
        # encoding
        jstr = mydumps(rootItem)
        
        print(jstr)
        
        #testItem = json.loads(jstr, object_hook=jsonAsCti) # decoding
        testItem = json.loads(jstr, cls=CtiDecoder) # decoding
        
        print("rootItem: {!r}".format(rootItem))
        print("testItem: {!r}".format(testItem))

        print(mydumps(testItem))    
        print(type(rootItem))
        print(type(testItem))
        print(type(testItem) == type(rootItem))
        assert (testItem == rootItem), "FAIL"
        
    def main2():
        
        a = {5: 'five', 6:'six'}
        b = {5: 'five', 6:'six'}
        
        print (a==b)
        
        
if __name__ == "__main__":
    main1()
        
