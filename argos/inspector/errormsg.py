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

""" Inspector that only shows an (error) message
"""
import logging

from argos.config.groupcti import MainGroupCti

from argos.inspector.abstract import AbstractInspector
from argos.utils.cls import check_is_a_string


logger = logging.getLogger(__name__)


class ErrorMsgInspector(AbstractInspector):
    """ Inspector that shows an error message

        :param str msg: the string that will be
    """
    def __init__(self, collector, msg, parent=None):

        super(ErrorMsgInspector, self).__init__(collector, parent=parent)

        check_is_a_string(msg)
        self.msg = msg

        self._config = self._createConfig()

        self.setCurrentIndex(self.ERROR_PAGE_IDX)


    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple()


    def _createConfig(self):
        """ Creates a config tree item (CTI) hierarchy containing default children.
        """
        rootItem = MainGroupCti('message inspector')
        return rootItem


    def updateContents(self, reason=None, initiator=None):
        """ Override updateContents. Shows the error message
        """
        self.setCurrentIndex(self.ERROR_PAGE_IDX)
        self._showError(msg=self.msg, title="Error")

