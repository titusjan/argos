#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests functionality from the utils package

"""

import unittest
from json import loads

from argos import configBasicLogging
from argos.utils.cls import is_a_string, is_text, is_binary
from argos.utils.misc import python2
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

        if python2():
            self.assertTrue(is_a_string(self.b_lit))
            self.assertTrue(is_a_string(self.np_b_lit))
        else:
            self.assertFalse(is_a_string(self.b_lit))
            self.assertFalse(is_a_string(self.np_b_lit))

        self.assertTrue(is_a_string(self.s_lit))
        self.assertTrue(is_a_string(self.np_s_lit))

        self.assertTrue(is_a_string(self.u_lit))
        self.assertTrue(is_a_string(self.np_u_lit))


    def test_is_text(self):
        """
            Result             py-2  py-3
            -----------------  ----- -----
            b'bytes literal'   False False
             'string literal'  False True
            u'unicode literal' True  True
        """

        self.assertFalse(is_text(self.b_lit))
        self.assertFalse(is_text(self.np_b_lit))

        if python2():
            self.assertFalse(is_text(self.s_lit))
            self.assertFalse(is_text(self.np_s_lit))
        else:
            self.assertTrue(is_text(self.s_lit))
            self.assertTrue(is_text(self.np_s_lit))

        self.assertTrue(is_text(self.u_lit))
        self.assertTrue(is_text(self.np_u_lit))


    def test_is_binary(self):
        """
            Result             py-2  py-3
            -----------------  ----- -----
            b'bytes literal'   True  True
             'string literal'  True  False
            u'unicode literal' False False
        """

        self.assertTrue(is_binary(self.b_lit))
        self.assertTrue(is_binary(self.np_b_lit))

        if python2():
            self.assertTrue(is_binary(self.s_lit))
            self.assertTrue(is_binary(self.np_s_lit))
        else:
            self.assertFalse(is_binary(self.s_lit))
            self.assertFalse(is_binary(self.np_s_lit))

        self.assertFalse(is_binary(self.u_lit))
        self.assertFalse(is_binary(self.np_u_lit))




    def tearDown(self):
        pass


if __name__ == '__main__':
    configBasicLogging(level='DEBUG')
    unittest.main()


