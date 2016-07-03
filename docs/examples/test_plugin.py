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

""" Test Rti
"""

import logging, os


from libargos.qt import QtGui
from libargos.repo.baserti import (ICONS_DIRECTORY, BaseRti)

logger = logging.getLogger(__name__)


class TestFileRti(BaseRti):
    """ Repository tree item for testing
    """
    _label = "HDF File"
    _iconOpen = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'memory.folder-open.svg'))
    _iconClosed = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'memory.folder-closed.svg'))

    def __init__(self, nodeName='', fileName=''):
        """ Constructor
        """
        super(TestFileRti, self).__init__(nodeName=nodeName, fileName=fileName)
        self._checkFileExists()


#    def _openResources(self):
#        """ Opens the root Dataset.
#        """
#        logger.info("Opening: {}".format(self._fileName))
#        self._dataset = Dataset(self._fileName)
#
#    def _closeResources(self):
#        """ Closes the root Dataset.
#        """
#        logger.info("Closing: {}".format(self._fileName))
#        self._dataset.close()
#        self._dataset = None
