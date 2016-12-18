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

""" Contains the RtiIconFactory
"""
from __future__ import print_function
import logging, os

from argos.qt import Qt, QtCore, QtGui, QtWidgets, QtSvg
from argos.info import program_directory, DEBUGGING
from argos.utils.cls import check_class

logger = logging.getLogger(__name__)



class RtiIconFactory(object):
    """ A factory class that generates QIcons for use in the Repository Tree.

        Typically the RepoTreeItems have a reference to a (singleton) RtiIconFactory and
        call getIcon to get an icon of a certain glyph, color and open/close state.

        The factory contains a icon registry that contains for registered (glyph, open/close state)
        combinations the location of an SVG file. The SVG files originate from the snip-icon
        library. See http://www.snipicons.com/

        The getIcon method can optionally set the fill color of the icons. It also caches the
        generated QItem objects to that they only have to be created once.
    """

    ICONS_DIRECTORY = os.path.join(program_directory(), 'img/snipicons')
    #ICON_SIZE = 32 # Render in this size

    # File state
    OPEN = "open"
    CLOSED = "closed"

    # Registered glyph names
    ERROR = "error"
    FOLDER = "folder"
    FILE = "file"
    ARRAY = "array"
    FIELD = "field"
    DIMENSION = "dimension"
    SEQUENCE = "sequence"
    SCALAR = "scalar"

    # Icon colors
    COLOR_ERROR      = '#FF0000'
    COLOR_UNKNOWN    = '#999999'
    #COLOR_MEMORY     = '#FFAA00'
    #COLOR_MEMORY     = '#FFFF40'
    COLOR_MEMORY     = '#FFDD20'

    _singleInstance = None

    def __init__(self):
        """ Constructor
        """
        self._icons = {}
        self._registry = {}
        self.colorsToBeReplaced = ('#008BFF', '#00AAFF')
        self.renderSizes = [16, 24, 32, 64]

        self.registerIcon(None, None) # no icon
        self.registerIcon("",   None) # no icon
        self.registerIcon("warning-sign.svg", self.ERROR)
        self.registerIcon("folder-open.svg",  self.FOLDER, True)
        self.registerIcon("folder-close.svg", self.FOLDER, False)
        self.registerIcon("file.svg",         self.FILE, True)
        self.registerIcon("file-inverse.svg", self.FILE, False)
        self.registerIcon("th-large.svg",     self.ARRAY)
        self.registerIcon("asterisk.svg",     self.FIELD)
        self.registerIcon("move.svg",         self.DIMENSION)
        self.registerIcon("align-left.svg",   self.SEQUENCE)
        self.registerIcon("leaf.svg",         self.SCALAR)


    @classmethod
    def singleton(cls):
        """ Returns the RtiIconFactory singleton.
        """
        if cls._singleInstance is None:
            cls._singleInstance = cls()
        return cls._singleInstance


    def registerIcon(self, fileName, glyph, isOpen=None):
        """ Register an icon SVG file given a glyph, and optionally the open/close state.

            :param fileName: filename to the SVG file.
                If the filename is a relative path, the ICONS_DIRECTORY will be prepended.
            :param glyph: a string describing the glyph (e.g. 'file', 'array')
            :param isOpen: boolean that indicates if the RTI is open or closed.
                If None, the icon will be registered for open is both True and False
            :return: QIcon
        """
        check_class(isOpen, bool, allow_none=True)

        if fileName and not os.path.isabs(fileName):
            fileName = os.path.join(self.ICONS_DIRECTORY, fileName)

        if isOpen is None:
            # Register both opened and closed variants
            self._registry[(glyph, True)] = fileName
            self._registry[(glyph, False)] = fileName
        else:
            self._registry[(glyph, isOpen)] = fileName


    def getIcon(self, glyph, isOpen, color=None):
        """ Returns a QIcon given a glyph name, open/closed state and color.

            The reslulting icon is cached so that it only needs to be rendered once.

            :param glyph: name of a registered glyph (e.g. 'file', 'array')
            :param isOpen: boolean that indicates if the RTI is open or closed.
            :param color: '#RRGGBB' string (e.g. '#FF0000' for red)
            :return: QtGui.QIcon
        """
        try:
            fileName = self._registry[(glyph, isOpen)]
        except KeyError:
            logger.warn("Unregistered icon glyph: {} (open={})".format(glyph, isOpen))
            from argos.utils.misc import log_dictionary
            log_dictionary(self._registry, "registry", logger=logger)
            raise

        return self.loadIcon(fileName, color=color)


    def loadIcon(self, fileName, color=None):
        """ Reads SVG from a file name and creates an QIcon from it.

            Optionally replaces the color. Caches the created icons.

            :param fileName: absolute path to an icon file.
                If False/empty/None, None returned, which yields no icon.
            :param color: '#RRGGBB' string (e.g. '#FF0000' for red)
            :return: QtGui.QIcon
        """
        if not fileName:
            return None

        key = (fileName, color)
        if key not in self._icons:
            try:
                with open(fileName, 'r') as input:
                    svg = input.read()

                self._icons[key] = self.createIconFromSvg(svg, color=color)
            except Exception as ex:
                # It's preferable to show no icon in case of an error rather than letting
                # the application fail. Icons are a (very) nice to have.
                logger.warn("Unable to read icon: {}".format(ex))
                if DEBUGGING:
                    raise
                else:
                    return None

        return self._icons[key]


    def createIconFromSvg(self, svg, color=None, colorsToBeReplaced=None):
        """ Creates a QIcon given an SVG string.

            Optionally replaces the colors in colorsToBeReplaced by color.

            :param svg: string containing Scalable Vector Graphics XML
            :param color: '#RRGGBB' string (e.g. '#FF0000' for red)
            :param colorsToBeReplaced: optional list of colors to be replaced by color
                If None, it will be set to the fill colors of the snip-icon libary
            :return: QtGui.QIcon
        """
        if colorsToBeReplaced is None:
            colorsToBeReplaced = self.colorsToBeReplaced

        if color:
            for oldColor in colorsToBeReplaced:
                svg = svg.replace(oldColor, color)

        # From http://stackoverflow.com/questions/15123544/change-the-color-of-an-svg-in-qt
        qByteArray = QtCore.QByteArray()
        qByteArray.append(svg)
        svgRenderer = QtSvg.QSvgRenderer(qByteArray)
        icon = QtGui.QIcon()
        for size in self.renderSizes:
            pixMap = QtGui.QPixmap(QtCore.QSize(size, size))
            pixMap.fill(Qt.transparent)
            pixPainter = QtGui.QPainter(pixMap)
            pixPainter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)
            pixPainter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            svgRenderer.render(pixPainter)
            pixPainter.end()
            icon.addPixmap(pixMap)

        return icon
