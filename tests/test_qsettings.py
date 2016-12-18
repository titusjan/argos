#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_argos
----------------------------------

Tests for `argos` module.
"""
import sys
import unittest

sys.path.append('..')
#print(sys.path)

from argos.qt import QtCore, getQApplicationInstance, USE_PYQT


class TestArgos(unittest.TestCase):

    def setUp(self):
        self.app = getQApplicationInstance()

        self.groupName = '__test__'
        self.qs = QtCore.QSettings()
        self.qs.remove(self.groupName) # start with clean slate
        self.qs.beginGroup(self.groupName)


    def test_read_write(self):

        self.qs.setValue('int', -6)
        self.assertEqual(-6, self.qs.value('int'))

        self.qs.setValue('float', 7.7)
        self.assertEqual(7.7, self.qs.value('float'))

        self.qs.setValue('str', 'six')
        self.assertEqual('six', self.qs.value('str'))

        large_str = '0123456789' * 10000
        self.qs.setValue('large_str', large_str)
        self.assertEqual(large_str, self.qs.value('large_str'))

        for p in range(5):
            n = pow(10, p)
            arr = range(n)
            name = 'arr10pow{}'.format(p)
            self.qs.setValue(name, arr)
            print("\np={}, n={}".format(p, n))
            print(repr(arr))
            print(repr(self.qs.value(name)))
            self.assertEqual(arr, arr)



    def tearDown(self):
        self.qs.endGroup()
        self.qs.remove(self.groupName)


if __name__ == '__main__':
    print ('Using: {}'.format('PyQt' if USE_PYQT else 'PySide'))
    unittest.main()

