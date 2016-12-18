#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest, logging, sys
import numpy as np

from numpy.testing import assert_array_equal
from argos import configBasicLogging
from argos.repo.memoryrtis import ArrayRti



class TestUntypedCtis(unittest.TestCase):

    def setUp(self):
        self.arr = np.arange(24).reshape(6, 4)
        self.rti = ArrayRti(self.arr, 'my array')


    def test_indexing(self):
        """ Test indexing and slicing
        """

        self.assertEqual(self.rti[2, 1], self.arr[2, 1])
        assert_array_equal(self.rti[:], self.arr[:])
        assert_array_equal(self.rti[2:5, :], self.arr[2:5, :])
        assert_array_equal(self.rti[-1], self.arr[-1])

        # Multidimensional indexing
        idx0 = [1, 1, 3]
        idx1 = [0, -1, 2]
        assert_array_equal(self.rti[idx0, idx1], self.arr[idx0, idx1])

        slices = [slice(2, None), 1]
        assert_array_equal(self.rti[slices], self.arr[slices])

        slices = tuple([slice(2), slice(1)])
        assert_array_equal(self.rti[slices], self.arr[slices])



if __name__ == '__main__':
    configBasicLogging(level='DEBUG')
    unittest.main()


