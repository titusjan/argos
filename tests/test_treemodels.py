#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest, logging, sys

from argos.qt.treemodels import BaseTreeModel
from argos.qt.treeitems import BaseTreeItem


class TestTreeItemGetByPath(unittest.TestCase):


    def setUp(self):

        self.rootItem = BaseTreeItem('root')
        self.item0 = self.rootItem.insertChild(BaseTreeItem('item0'))
        self.item1 = self.item0.insertChild(BaseTreeItem('item1'))
        self.item1a = self.item0.insertChild(BaseTreeItem('item1a'))
        self.item2 = self.item1.insertChild(BaseTreeItem('item2'))
        self.item3 = self.rootItem.insertChild(BaseTreeItem('item3'))


    def testStartAtItem(self):

        # Normal use
        checkItem = self.rootItem.findByNodePath('item3')
        self.assertIs(checkItem, self.item3)

        # Long path
        checkItem = self.rootItem.findByNodePath('item0/item1/item2')
        self.assertIs(checkItem, self.item2)

        # Leading slash
        self.assertRaises(AssertionError, self.rootItem.findByNodePath, '/item3')

        # Trailing slash
        checkItem = self.rootItem.findByNodePath('item3/')
        self.assertIs(checkItem, self.item3)

        # Long path with double slashes
        checkItem = self.rootItem.findByNodePath('item0///item1//')
        self.assertIs(checkItem, self.item1)

        # Item not found
        self.assertRaises(IndexError, self.rootItem.findByNodePath, 'item0/narf//')

        # Empty string
        self.assertRaises(IndexError, self.rootItem.findByNodePath, '')

        # None-strings
        self.assertRaises(TypeError, self.rootItem.findByNodePath, 444)


class TestGetByPath(unittest.TestCase):


    def setUp(self):

        self.model = BaseTreeModel()

        self.item0, self.index0 = self.insertBaseTreeItem('item0')
        self.item1, self.index1 = self.insertBaseTreeItem('item1', self.index0)
        self.item1a, self.index1a = self.insertBaseTreeItem('item1a', self.index0)
        self.item2, self.index2 = self.insertBaseTreeItem('item2', self.index1)

        self.item3, self.index3 = self.insertBaseTreeItem('item3')


    def tearDown(self):
        pass

    def insertBaseTreeItem(self, nodeName, parentIndex=None):
        "Inserts a new BaseTreeItem item in the model"
        item = BaseTreeItem(nodeName=nodeName)
        index = self.model.insertItem(item, parentIndex=parentIndex)
        return item, index

    def getLastItem(self, path, startIndex=None):
        """ Gets the last item from the itemAndIndexPath
        """
        iiPath = self.model.findItemAndIndexPath(path, startIndex=startIndex)
        return iiPath[-1]

    def testLastPathItemStartAtRoot(self):

        # Normal use
        checkItem, checkIndex = self.getLastItem('item3')
        self.assertIs(self.model.getItem(checkIndex), checkItem)
        self.assertIs(checkItem, self.item3)

        # Long path
        checkItem, checkIndex = self.getLastItem('item0/item1/item2')
        self.assertIs(self.model.getItem(checkIndex), checkItem)
        self.assertIs(checkItem, self.item2)

        # Leading slash
        checkItem, checkIndex = self.getLastItem('/item3')
        self.assertIs(self.model.getItem(checkIndex), checkItem)
        self.assertIs(checkItem, self.item3)

        # Trailing slash
        checkItem, checkIndex = self.getLastItem('item3/')
        self.assertIs(self.model.getItem(checkIndex), checkItem)
        self.assertIs(checkItem, self.item3)

        # Long path with double slashes
        checkItem, checkIndex = self.getLastItem('/item0///item1//')
        self.assertIs(self.model.getItem(checkIndex), checkItem)
        self.assertIs(checkItem, self.item1)

        # Item not found
        self.assertRaises(IndexError, self.getLastItem, '/item0/narf//')

        # Invisible root
        checkItem, checkIndex = self.getLastItem('/')
        self.assertFalse(checkIndex.isValid())
        self.assertIs(checkItem, self.model.invisibleRootItem)

        # Empty string
        self.assertRaises(IndexError, self.getLastItem, '')

        # None-strings
        self.assertRaises(TypeError, self.getLastItem, 444)


    def testLastPathItemStartAtIndex(self):

        # Sanity check
        self.assertRaises(IndexError, self.getLastItem, 'item1/item2')

        # Normal use
        checkItem, checkIndex = self.getLastItem('item1/item2', startIndex=self.index0)
        self.assertIs(self.model.getItem(checkIndex), checkItem)
        self.assertIs(checkItem, self.item2)

        # Starting slash starts at root
        checkItem, checkIndex = self.getLastItem('/item0/item1/item2', startIndex=self.index0)
        self.assertIs(self.model.getItem(checkIndex), checkItem)
        self.assertIs(checkItem, self.item2)


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG', stream=sys.stderr,
                        format='%(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-7s: %(message)s')
    unittest.main()


