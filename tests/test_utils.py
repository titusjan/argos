#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests functionality from the utils package

"""

import unittest

from argos.utils.cls import isAString, isBinary
import numpy as np


class TestStringTypeDetection(unittest.TestCase):
    """ Tests if the is_a_string and comparable function work

        The test should work on both Python-2 and Python-3

    """

    def setUp(self):
        pass
        self.b_lit = b'bytes literal'
        self.s_lit = 'literal literal'
        self.u_lit = u'unicode literal'

        self.np_b_lit = np.bytes_('numpy bytes literal')
        self.np_s_lit = np.str_('numpy unicode literal')
        self.np_u_lit = np.unicode_('numpy unicode literal')


    def test_is_a_string(self):
        """
            Result             py-2  py-3
            -----------------  ----- -----
            b'bytes literal'   True  False
             'string literal'  True  True
            u'unicode literal' True  True
        """
        self.assertFalse(isAString(self.b_lit))
        self.assertFalse(isAString(self.np_b_lit))

        self.assertTrue(isAString(self.s_lit))
        self.assertTrue(isAString(self.np_s_lit))

        self.assertTrue(isAString(self.u_lit))
        self.assertTrue(isAString(self.np_u_lit))




    def test_is_binary(self):
        """
            Result             py-2  py-3
            -----------------  ----- -----
            b'bytes literal'   True  True
             'string literal'  True  False
            u'unicode literal' False False
        """

        self.assertTrue(isBinary(self.b_lit))
        self.assertTrue(isBinary(self.np_b_lit))

        self.assertFalse(isBinary(self.s_lit))
        self.assertFalse(isBinary(self.np_s_lit))

        self.assertFalse(isBinary(self.u_lit))
        self.assertFalse(isBinary(self.np_u_lit))




    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()


