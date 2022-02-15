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

""" Defines a global Inspector registry to register inspector plugins.
"""

import logging

from argos.info import DEBUGGING
from argos.reg.basereg import BaseRegItem, BaseRegistry, RegType

logger = logging.getLogger(__name__)

DEFAULT_INSPECTOR = 'Table'

class InspectorRegItem(BaseRegItem):
    """ Class to keep track of a registered Inspector.
        Has a create() method that functions as an Inspector factory.
    """
    FIELDS  = BaseRegItem.FIELDS[:1] + ['shortCut'] + BaseRegItem.FIELDS[1:]
    TYPES   = BaseRegItem.TYPES[:1] + [RegType.ShortCut] + BaseRegItem.TYPES[1:]
    LABELS  = BaseRegItem.LABELS[:1] + ['Shortcut'] + BaseRegItem.LABELS[1:]
    STRETCH = BaseRegItem.STRETCH[:1] + [False] + BaseRegItem.STRETCH[1:]


    def __init__(self, name='', absClassName='', pythonPath='', shortCut=''):
        """ Constructor. See the ClassRegItem class doc string for the parameter help.
        """
        super(InspectorRegItem, self).__init__(name=name, absClassName=absClassName,
                                               pythonPath=pythonPath)
        self._data['shortCut'] = shortCut


    @property
    def shortCut(self):
        """ Keyboard short cut
        """
        return self._data['shortCut']


    @property
    def axesNames(self):
        """ The axes names of the inspector.
        """
        return [] if self.cls is None else self.cls.axesNames()

    @property
    def nDims(self):
        """ The number of axes of this inspector.
        """
        return len(self.axesNames)


    def create(self, collector, tryImport=True):
        """ Creates an inspector of the registered and passes the collector to the constructor.
            Tries to import the class if tryImport is True.
            Raises ImportError if the class could not be imported.
        """
        cls = self.getClass(tryImport=tryImport)
        if not self.successfullyImported:
            raise ImportError("Class not successfully imported: {}".format(self.exception))
        return cls(collector)



class InspectorRegistry(BaseRegistry):
    """ Class that maintains the collection of registered inspector classes.
        See the base class documentation for more info.
    """
    ITEM_CLASS = InspectorRegItem

    def __init__(self):
        """ Constructor
        """
        super(InspectorRegistry, self).__init__()


    @property
    def registryName(self):
        """ Human readable name for this registry.
        """
        return "Inspector"


    def getDefaultItems(self):
        """ Returns a list with the default plugins in the inspector registry.
        """
        plugins = [
            InspectorRegItem('Line Plot',
                             'argos.inspector.pgplugins.lineplot1d.PgLinePlot1d',
                             shortCut='Ctrl+1'),
            InspectorRegItem('Image Plot',
                             'argos.inspector.pgplugins.imageplot2d.PgImagePlot2d',
                             shortCut='Ctrl+2'),
            InspectorRegItem(DEFAULT_INSPECTOR,
                             'argos.inspector.qtplugins.table.TableInspector',
                             shortCut='Ctrl+3'),
            InspectorRegItem('Text',
                             'argos.inspector.qtplugins.text.TextInspector',
                             shortCut='Ctrl+4'),
            ]
        if DEBUGGING:
            plugins.append(InspectorRegItem('Image Plot (Old)',
                                            'argos.inspector.pgplugins.old_imageplot2d.PgImagePlot2d'))
            plugins.append(InspectorRegItem('Debug Inspector',
                                            'argos.inspector.debug.DebugInspector'))
        return plugins
