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

""" Plugins package.
"""

from libargos.state.registry import getGlobalRegistry


__registry = getGlobalRegistry()

__registry.registerRti('libargos.plugins.rti.ncdf.NcdfFileRti', 
                       extensions=['nc', 'nc3', 'nc4'])
__registry.registerRti('libargos.plugins.rti.nptextfile.NumpyTextFileRti', 
                       extensions=['txt', 'text'])

