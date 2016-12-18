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

""" Test inspector.
"""
import logging, os, sys


import argos
from argos.qt import initQCoreApplication
from argos.config.groupcti import MainGroupCti
from argos.inspector.abstract import AbstractInspector
from argos.inspector.registry import InspectorRegistry
from argos.qt import Qt, QtWidgets

logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

class BuggyInspector(AbstractInspector):
    """ Inspector that deliberately will not install.

        For testing and debugging purposes.
    """
    def __init__(self, collector, parent=None):

        super(BuggyInspector, self).__init__(collector, parent=parent)

        self.label = QtWidgets.QLabel()
        self.contentsLayout.addWidget(self.label)

        self._config = self._createConfig()


    @classmethod
    def axesNames(cls):
        """ The names of the axes that this inspector visualizes.
            See the parent class documentation for a more detailed explanation.
        """
        return tuple()


    def _createConfig(self):
        """ Creates a config tree item (CTI) hierarchy containing default children.
        """
        rootItem = MainGroupCti('inspector')
        return rootItem


    def _drawContents(self, reason=None, initiator=None):
        """ Draws the table contents from the sliced array of the collected repo tree item.

            The reason and initiator parameters are ignored.
            See AbstractInspector.updateContents for their description.
        """
        logger.debug("BuggyInspector._drawContents: {}".format(self))


def persistentRegisterInspector(fullName, fullClassName, pythonPath=''):
    """ Registers an inspector

        Loads or inits the inspector registry, register the inspector and saves the settings.
        Important: instantiate a Qt application first to use the correct settings file/winreg.
    """
    registry = InspectorRegistry()
    registry.loadOrInitSettings()
    registry.registerInspector(fullName, fullClassName, pythonPath=pythonPath)
    registry.saveSettings()



if __name__ == "__main__":
    argos.configBasicLogging(level='DEBUG')
    initQCoreApplication()
    persistentRegisterInspector('Buggy inspector', 'BuggyInspector')


