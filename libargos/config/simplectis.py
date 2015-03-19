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

""" Some simple Config Tree Items
"""
import logging

from .basecti import BaseCti


logger = logging.getLogger(__name__)


class DefaultValue(object):
    """ Class for DEFAULT_VALUE constant. 
    """
    pass
    
DEFAULT_VALUE = DefaultValue()
    

class IntegerCti(BaseCti):
    """ Config Tree Item to store an integer.
    """
    def __init__(self, nodeName='', value=DEFAULT_VALUE, defaultValue=None):
        """ Constructor
            :param nodeName: name of this node (used to construct the node path).
            :param value: the configuration value. If omitted the defaultValue will be used.
            :param defaultValue: default value to which the value can be reset or initialized
                if omitted  from the constructor
        """
        super(IntegerCti, self).__init__(nodeName=nodeName)

        self._defaultValue = defaultValue
        self._value = DEFAULT_VALUE # to make pylint happy
        self.value = value
         
        self.minValue = 0
        self.maxValue = 100
        
        