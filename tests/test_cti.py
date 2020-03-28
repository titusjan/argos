#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest, copy
from json import loads, dumps


from argos.qt import QtWidgets, QtGui
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
    unittest.main()


