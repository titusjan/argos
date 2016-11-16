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

""" Plugins that use the PyQtGraph plot library.

    The default plugins are created (on registry reset) by InspectorRegistry.getDefaultItems()
"""
try:
    import pyqtgraph as pg
except Exception as ex:
    raise ImportError("PyQtGraph 0.10.0 or higher required")


import logging

logger = logging.getLogger(__name__)

logger.debug("Imported PyQtGraph: {}".format(pg.__version__))


def setPgConfigOptions(**kwargs):
    """ Sets the PyQtGraph config options and emits a log message
    """
    for key, value in kwargs.items():
        logger.debug("Setting PyQtGraph config option: {} = {}".format(key, value))

    pg.setConfigOptions(**kwargs)


# Sets some config options
setPgConfigOptions(exitCleanup=False, crashWarning=True,
                   antialias=False,     # Anti aliasing of lines having width > 1 may be slow (OS-X)
                   leftButtonPan=True,  # If False, left button drags a rubber band for zooming
                   foreground='k',      # Default foreground color for axes, labels, etc.
                   background='w')      # Default background for GraphicsWidget


