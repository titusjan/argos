#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest, logging, sys
from json import loads

from libargos.qt import QtCore, QtGui
from libargos.config.basecti import BaseCti, ctiDumps, CtiDecoder
from libargos.config.simplectis import ColorCti



class TestBaseCtis(unittest.TestCase):

    def setUp(self):
        self.rootItem = BaseCti(nodeName='<invisible-root>', data=0.123456789012345678901234567890)
        self.rootItem.insertChild(BaseCti(nodeName='kid', data=-7))


    def test__eq__(self):
        
        ctiIn = BaseCti('parent', 7, defaultData=7)
        self.assertEqual(ctiIn, ctiIn)
        self.assertEqual(ctiIn, BaseCti('parent', 7, defaultData=7))

        self.assertNotEqual(ctiIn, BaseCti('parent', 7, defaultData=9))
        self.assertNotEqual(ctiIn, BaseCti('parent', 9, defaultData=7))

        ctiOut = BaseCti('parent', 7, defaultData=7)
        ctiIn.insertChild(BaseCti('kid', 22, defaultData=23))
        self.assertNotEqual(ctiIn, ctiOut)

        ctiOut.insertChild(BaseCti('kid', 22, defaultData=23))
        self.assertEqual(ctiIn, ctiOut)

        ctiIn.childItems[0].data = 99    
        self.assertNotEqual(ctiIn, ctiOut)
        

    def testJson(self):
        
        # encoding
        jstr = ctiDumps(self.rootItem)
        #print(jstr)
        
        # decoding
        #testItem = json.loads(jstr, object_hook=jsonAsCti)
        testItem = loads(jstr, cls=CtiDecoder)
        #print(mydumps(testItem))
            
        self.assertEqual(testItem, self.rootItem)


    def testNonDefaults(self):
        
        # A data different than its default should be restored 
        ctiIn  = BaseCti('parent', 6, defaultData=7)
        defDict = ctiIn.getNonDefaultsDict()
        #print(defDict)
        ctiOut = BaseCti('parent', defaultData=7)
        ctiOut.setValuesFromDict(defDict)
        self.assertEqual(ctiIn, ctiOut)
        
        # A data is not written if it's the default and 
        # is read correctly if the default stays the same 
        ctiIn  = BaseCti('parent', 7, defaultData=7)
        defDict = ctiIn.getNonDefaultsDict()
        print(defDict)
        ctiOut = BaseCti('parent', defaultData=7)
        ctiOut.setValuesFromDict(defDict)
        self.assertEqual(ctiIn, ctiOut)
        
        # A default data should have no effect it the default changes in the future.
        ctiIn  = BaseCti('parent', 7, defaultData=7)
        defDict = ctiIn.getNonDefaultsDict()
        #print(defDict)
        ctiOut = BaseCti('parent', defaultData=9)
        ctiOut.setValuesFromDict(defDict)
        self.assertNotEqual(ctiIn, ctiOut)

        # Test children
        ctiIn  = BaseCti('parent', defaultData=6)
        ctiIn.insertChild(BaseCti('child1', 1, defaultData=1))
        ctiIn.insertChild(BaseCti('child2', 3, defaultData=2))
        defDict = ctiIn.getNonDefaultsDict()
        #print(defDict)
        ctiOut = BaseCti('parent', defaultData=6)
        ctiOut.insertChild(BaseCti('child1', defaultData=1))
        ctiOut.insertChild(BaseCti('child2', defaultData=2))
        ctiOut.setValuesFromDict(defDict)
        self.assertEqual(ctiIn, ctiOut)


    def tearDown(self):
        pass



class TestSimpleCtis(unittest.TestCase):

    def setUp(self):
        self.rootItem = BaseCti(nodeName='<invisible-root>', data=0.123456789012345678901234567890)
        self.rootItem.insertChild(BaseCti(nodeName='kid', data=-7))


    def tearDown(self):
        pass

    def testColorCti(self):
        
        colorStr = '#FF33EE'
        cti = ColorCti('color', defaultData=colorStr)
        self.assertEqual(cti.data, QtGui.QColor(colorStr))
        self.assertEqual(cti.value, QtGui.QColor(colorStr))
        self.assertEqual(cti.displayValue, colorStr)


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG', stream=sys.stderr,
                        format='%(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-7s: %(message)s')    
    unittest.main()
    
    