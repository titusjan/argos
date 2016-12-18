#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest, logging, sys, copy
from json import loads, dumps

from argos import configBasicLogging
from argos.qt import QtWidgets
from argos.config.abstractcti import ctiDumps, CtiDecoder
from argos.config.untypedcti import UntypedCti
from argos.config.qtctis import ColorCti



class TestUntypedCtis(unittest.TestCase):

    def setUp(self):
        self.invisibleRootItem = UntypedCti(nodeName='<invisible-root>', defaultData=0.123456789012345678901234567890)
        self.invisibleRootItem.insertChild(UntypedCti(nodeName='kid', defaultData=-7))


    def test__eq__(self):

        ctiIn = UntypedCti('parent', defaultData=7)
        self.assertEqual(ctiIn, ctiIn)
        self.assertEqual(ctiIn, UntypedCti('parent', defaultData=7))

        self.assertNotEqual(ctiIn, UntypedCti('parent', defaultData=9))

        ctiOut = UntypedCti('parent', defaultData=7)
        ctiIn.insertChild(UntypedCti('kid', defaultData=23))
        self.assertNotEqual(ctiIn, ctiOut)

        ctiOut.insertChild(UntypedCti('kid', defaultData=23))
        self.assertEqual(ctiIn, ctiOut)

        ctiIn.childItems[0].data = 99
        self.assertNotEqual(ctiIn, ctiOut)


    # This functionality is currently not used? Depricated?
    def __not_used__testJson(self):

        # encoding
        jstr = ctiDumps(self.invisibleRootItem)
        #print(jstr)

        # decoding
        #testItem = json.loads(jstr, object_hook=jsonAsCti)
        testItem = loads(jstr, cls=CtiDecoder)
        #print(mydumps(testItem))

        self.assertEqual(testItem, self.invisibleRootItem)


    def testNonDefaults(self):

        # A data different than its default should be restored
        ctiIn  = UntypedCti('parent', defaultData=7)
        defDict = ctiIn.getNonDefaultsDict()
        #print(defDict)
        ctiOut = UntypedCti('parent', defaultData=7)
        ctiOut.setValuesFromDict(defDict)
        self.assertEqual(ctiIn, ctiOut)

        # A data is not written if it's the default and
        # is read correctly if the default stays the same
        ctiIn  = UntypedCti('parent', defaultData=7)
        defDict = ctiIn.getNonDefaultsDict()
        #print(defDict)
        ctiOut = UntypedCti('parent', defaultData=7)
        ctiOut.setValuesFromDict(defDict)
        self.assertEqual(ctiIn, ctiOut)

        # A default data should have no effect it the default changes in the future.
        ctiIn  = UntypedCti('parent', defaultData=7)
        defDict = ctiIn.getNonDefaultsDict()
        #print(defDict)
        ctiOut = UntypedCti('parent', defaultData=9)
        ctiOut.setValuesFromDict(defDict)
        self.assertNotEqual(ctiIn, ctiOut)

        # Test children
        ctiIn  = UntypedCti('parent', defaultData=6)
        ctiIn.insertChild(UntypedCti('child1', defaultData=1))
        ctiIn.insertChild(UntypedCti('child2', defaultData=2))
        defDict = ctiIn.getNonDefaultsDict()
        #print(defDict)
        ctiOut = UntypedCti('parent', defaultData=6)
        ctiOut.insertChild(UntypedCti('child1', defaultData=1))
        ctiOut.insertChild(UntypedCti('child2', defaultData=2))
        ctiOut.setValuesFromDict(defDict)
        self.assertEqual(ctiIn, ctiOut)


    def tearDown(self):
        pass



class TestSimpleCtis(unittest.TestCase):

    def setUp(self):
        self.invisibleRootItem = UntypedCti(nodeName='<invisible-root>', defaultData=0.123456789012345678901234567890)
        self.invisibleRootItem.insertChild(UntypedCti(nodeName='kid', defaultData=-7))

    def tearDown(self):
        pass


    def testColorCti(self):

        colorStr = '#FF33EE'
        cti = ColorCti('color', defaultData=colorStr)
        self.assertEqual(cti.data, QtGui.QColor(colorStr))
        self.assertEqual(cti.data, QtGui.QColor(colorStr))
        self.assertEqual(cti.displayValue, colorStr)


    def closedLoop(self, ctiIn):
        """ serialize cti default values to json and back
        """
        nonDefaults = ctiIn.getNonDefaultsDict()
        json = dumps(nonDefaults)
        valuesDict = loads(json)

        ctiOut = copy.deepcopy(ctiIn)
        ctiOut._data = None
        ctiOut.setValuesFromDict(valuesDict)
        return ctiOut


    def testClosedLoop(self):
        # A data different than its default should be restored
        ctiIn  = ColorCti('parent', defaultData='#ABCDEF')
        ctiIn.data='#DEADBE' # works only if data is set, otherwise ctiOut.data will be None
        ctiOut = self.closedLoop(ctiIn)
        print("ctiIn {}".format(ctiIn.__dict__))
        print("ctiOut {}".format(ctiOut.__dict__))
        self.assertEqual(ctiIn, ctiOut)


if __name__ == '__main__':
    configBasicLogging(level='DEBUG')
    unittest.main()


