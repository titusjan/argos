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

""" Contains the CTIs that represent Qt data types.
"""
import logging

from argos.config.abstractcti import AbstractCti, AbstractCtiEditor, InvalidInputError
from argos.config.boolcti import BoolCti
from argos.config.choicecti import ChoiceCti
from argos.config.intcti import IntCti
from argos.config.floatcti import FloatCti
from argos.info import DEBUGGING
from argos.qt import Qt, QtCore, QtGui, QtWidgets, QtSlot
from argos.utils.cls import check_is_a_string



logger = logging.getLogger(__name__)


PEN_STYLE_DISPLAY_VALUES = ('solid', 'dashed', 'dotted', 'dash-dot', 'dash-dot-dot')
PEN_STYLE_CONFIG_VALUES = (Qt.SolidLine, Qt.DashLine, Qt.DotLine,
                           Qt.DashDotLine, Qt.DashDotDotLine)


def createPenStyleCti(nodeName, defaultData=0, includeNone=False):
    """ Creates a ChoiceCti with Qt PenStyles.
        If includeEmtpy is True, the first option will be None.
    """
    displayValues=PEN_STYLE_DISPLAY_VALUES
    configValues=PEN_STYLE_CONFIG_VALUES
    if includeNone:
        displayValues = [''] + list(displayValues)
        configValues = [None] + list(configValues)
    return ChoiceCti(nodeName, defaultData,
                     displayValues=displayValues, configValues=configValues)


def createPenWidthCti(nodeName, defaultData=1.0, zeroValueText=None):
    """ Creates a FloatCti with defaults for configuring a QPen width.

        If specialValueZero is set, this string will be displayed when 0.0 is selected.
        If specialValueZero is None, the minValue will be 0.1
    """
    # A pen line width of zero indicates a cosmetic pen. This means that the pen width is
    # always drawn one pixel wide, independent of the transformation set on the painter.
    # Note that line widths other than 1 may be slow when anti aliasing is on.
    return FloatCti(nodeName, defaultData=defaultData, specialValueText=zeroValueText,
                    minValue=0.1 if zeroValueText is None else 0.0,
                    maxValue=100, stepSize=0.1, decimals=1)


def fontFamilyIndex(qFont, families):
    """ Searches the index of qFont.family in the families list.
        If qFont.family() is not in the list, the index of qFont.defaultFamily() is returned.
        If that is also not present an error is raised.
    """
    try:
        return families.index(qFont.family())
    except ValueError:
        if False and DEBUGGING:
            raise
        else:
            logger.warn("{} not found in font families, using default.".format(qFont.family()))
            return families.index(qFont.defaultFamily())


def fontWeightIndex(qFont, weights):
    """ Searches the index of qFont.family in the weight list.
        If qFont.weight() is not in the list, the index of QFont.Normal is returned.
        If that is also not present an error is raised.
    """
    try:
        return weights.index(qFont.weight())
    except ValueError:
        if False and DEBUGGING:
            raise
        else:
            logger.warn("{} not found in font weights, using normal.".format(qFont.weight()))
            return weights.index(QtGui.QFont.Normal)


class ColorCti(AbstractCti):
    """ Config Tree Item to store a color.
    """
    def __init__(self, nodeName, defaultData=''):
        """ Constructor.
            For the (other) parameters see the AbstractCti constructor documentation.
        """
        super(ColorCti, self).__init__(nodeName, defaultData)

    def _enforceDataType(self, data):
        """ Converts to str so that this CTI always stores that type.
        """
        qColor = QtGui.QColor(data)    # TODO: store a RGB string?
        if not qColor.isValid():
            raise ValueError("Invalid color specification: {!r}".format(data))
        return qColor

    def _dataToString(self, data):
        """ Conversion function used to convert the (default)data to the display value.
        """
        return data.name().upper()

    @property
    def decoration(self):
        """ Returns the data (QColor) to be displayed as decoration
        """
        return self.data


    def _nodeGetNonDefaultsDict(self):
        """ Retrieves this nodes` values as a dictionary to be used for persistence.
            Non-recursive auxiliary function for getNonDefaultsDict
        """
        dct = {}
        if self.data != self.defaultData:
            dct['data'] = self.data.name()
        return dct


    def _nodeSetValuesFromDict(self, dct):
        """ Sets values from a dictionary in the current node.
            Non-recursive auxiliary function for setValuesFromDict
        """
        if 'data' in dct:
            self.data = QtGui.QColor(dct['data'])


    def createEditor(self, delegate, parent, option):
        """ Creates a ColorCtiEditor.
            For the parameters see the AbstractCti constructor documentation.
        """
        return ColorCtiEditor(self, delegate, parent=parent)



class ColorCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a QCombobox for editing ColorCti objects.
    """
    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters
        """
        super(ColorCtiEditor, self).__init__(cti, delegate, parent=parent)

        lineEditor = QtWidgets.QLineEdit(parent)
        regExp = QtCore.QRegExp(r'#?[0-9A-F]{6}', Qt.CaseInsensitive)
        validator = QtGui.QRegExpValidator(regExp, parent=lineEditor)
        lineEditor.setValidator(validator)

        self.lineEditor = self.addSubEditor(lineEditor, isFocusProxy=True)

        pickButton = QtWidgets.QToolButton()
        pickButton.setText("...")
        pickButton.setToolTip("Open color dialog.")
        pickButton.setFocusPolicy(Qt.NoFocus)
        pickButton.clicked.connect(self.openColorDialog)

        self.pickButton = self.addSubEditor(pickButton)


    def finalize(self):
        """ Is called when the editor is closed. Disconnect signals.
        """
        self.pickButton.clicked.disconnect(self.openColorDialog)
        super(ColorCtiEditor, self).finalize()


    def openColorDialog(self):
        """ Opens a QColorDialog for the user
        """
        try:
            currentColor = self.getData()
        except InvalidInputError:
            currentColor = self.cti.data

        qColor = QtWidgets.QColorDialog.getColor(currentColor, self)

        if qColor.isValid():
            self.setData(qColor)
            self.commitAndClose()


    def setData(self, qColor):
        """ Provides the main editor widget with a data to manipulate.
        """
        self.lineEditor.setText(qColor.name().upper())


    def getData(self):
        """ Gets data from the editor widget.
        """
        text = self.lineEditor.text()
        if not text.startswith('#'):
            text = '#' + text

        validator = self.lineEditor.validator()
        if validator is not None:
            state, text, _ = validator.validate(text, 0)
            if state != QtGui.QValidator.Acceptable:
                raise InvalidInputError("Invalid input: {!r}".format(text))

        return  QtGui.QColor(text)


class FontCti(AbstractCti):
    """ Config Tree Item that configures a QFont

        The target font will be be updated by calling updateTarget (of the root CTI)
    """
    def __init__(self, targetWidget, nodeName='font', defaultData=None):
        """ Constructor.

            :param targetWidget: a QWidget that must have a setFont() method
            For the (other) parameters see the AbstractCti constructor documentation.
        """
        super(FontCti, self).__init__(nodeName,
                                defaultData=QtGui.QFont() if defaultData is None else defaultData)

        self._targetWidget = targetWidget

        self.familyCti = self.insertChild(
            FontChoiceCti("family", defaultFamily=self.defaultData.family()))

        self.pointSizeCti = self.insertChild(
            IntCti("size", self.defaultData.pointSize(),
                   minValue=1, maxValue=500, stepSize=1, suffix=' pt'))

        QtF = QtGui.QFont
        weights = [QtF.Light, QtF.Normal, QtF.DemiBold, QtF.Bold, QtF.Black]
        self.weightCti = self.insertChild(
            ChoiceCti("weight", defaultData=fontWeightIndex(self.defaultData, weights),
                      displayValues=['Light', 'Normal', 'DemiBold', 'Bold', 'Black'],
                      configValues=weights))

        self.italicCti = self.insertChild(BoolCti("italic", self.defaultData.italic()))


    def _enforceDataType(self, data):
        """ Converts to str so that this CTI always stores that type.
        """
        result = QtGui.QFont(data)
        return result


    @property
    def data(self):
        """ Returns the font of this item.
        """
        return self._data


    @data.setter
    def data(self, data):
        """ Sets the font data of this item.
            Does type conversion to ensure data is always of the correct type.

            Also updates the children (which is the reason for this property to be overloaded.
        """
        self._data = self._enforceDataType(data) # Enforce self._data to be a QFont
        self.familyCti.data = fontFamilyIndex(self.data, list(self.familyCti.iterConfigValues))
        self.pointSizeCti.data = self.data.pointSize()
        self.weightCti.data = fontWeightIndex(self.data, list(self.weightCti.iterConfigValues))
        self.italicCti.data = self.data.italic()


    @property
    def defaultData(self):
        """ Returns the default font of this item.
        """
        return self._defaultData


    @defaultData.setter
    def defaultData(self, defaultData):
        """ Sets the data of this item.
            Does type conversion to ensure default data is always of the correct type.
        """
        self._defaultData = self._enforceDataType(defaultData) # Enforce to be a QFont
        self.familyCti.defaultData = fontFamilyIndex(self.defaultData,
                                                     list(self.familyCti.iterConfigValues))
        self.pointSizeCti.defaultData = self.defaultData.pointSize()
        self.weightCti.defaultData = self.defaultData.weight()
        self.italicCti.defaultData = self.defaultData.italic()


    @property
    def displayValue(self):
        """ Returns the string representation of data for use in the tree view.
            Returns the empty string.
        """
        return ''


    @property
    def debugInfo(self):
        """ Returns the string representation of data for use in the tree view.
            Returns the empty string. If info.DEBUGGING is True, QFont.toString is used.
        """
        return self._dataToString(self.data)


    def _dataToString(self, data):
        """ Conversion function used to convert the (default)data to the display value.
        """
        return data.toString() # data is a QFont


    def _updateTargetFromNode(self):
        """ Applies the font config settings to the target widget's font.

            That is the targetWidget.setFont() is called with a font create from the config values.
        """
        font = self.data
        if self.familyCti.configValue:
            font.setFamily(self.familyCti.configValue)
        else:
            font.setFamily(QtGui.QFont().family()) # default family
        font.setPointSize(self.pointSizeCti.configValue)
        font.setWeight(self.weightCti.configValue)
        font.setItalic(self.italicCti.configValue)
        self._targetWidget.setFont(font)


    def _nodeGetNonDefaultsDict(self):
        """ Retrieves this nodes` values as a dictionary to be used for persistence.
            Non-recursive auxiliary function for getNonDefaultsDict
        """
        dct = {}
        if self.data != self.defaultData:
            dct['data'] = self.data.toString() # calls QFont.toString()
        return dct


    def _nodeSetValuesFromDict(self, dct):
        """ Sets values from a dictionary in the current node.
            Non-recursive auxiliary function for setValuesFromDict
        """
        if 'data' in dct:
            qFont = QtGui.QFont()
            success = qFont.fromString(dct['data'])
            if not success:
                msg = "Unable to create QFont from string {!r}".format(dct['data'])
                logger.warn(msg)
                if DEBUGGING:
                    raise ValueError(msg)
            self.data = qFont


    def createEditor(self, delegate, parent, option):
        """ Creates a FontCtiEditor.
            For the parameters see the AbstractCti documentation.
        """
        return FontCtiEditor(self, delegate, parent=parent)



class FontCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a label and a button for opening the Qt font dialog
    """
    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters
        """
        super(FontCtiEditor, self).__init__(cti, delegate, parent=parent)

        pickButton = QtWidgets.QToolButton()
        pickButton.setText("...")
        pickButton.setToolTip("Open font dialog.")
        pickButton.setFocusPolicy(Qt.NoFocus)
        pickButton.clicked.connect(self.execFontDialog)

        self.pickButton = self.addSubEditor(pickButton)

        if DEBUGGING:
            self.label = self.addSubEditor(QtWidgets.QLabel(self.cti.displayValue))
            labelSizePolicy = self.label.sizePolicy()
            self.label.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                     labelSizePolicy.verticalPolicy())


    def finalize(self):
        """ Is called when the editor is closed. Disconnect signals.
        """
        self.pickButton.clicked.disconnect(self.execFontDialog)
        super(FontCtiEditor, self).finalize()


    def execFontDialog(self):
        """ Opens a QColorDialog for the user
        """
        currentFont = self.getData()
        newFont, ok = QtGui.QFontDialog.getFont(currentFont, self)
        if ok:
            self.setData(newFont)
        else:
            self.setData(currentFont)
        self.commitAndClose()


    def setData(self, data):
        """ Provides the main editor widget with a data to manipulate.
        """
        # Set the data in the 'editor_data' property of the pickButton to that getData
        # can pass the same value back into the CTI. # TODO: use a member?
        self.pickButton.setProperty("editor_data", data)


    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.pickButton.property("editor_data")




class FontChoiceCti(ChoiceCti):
    """ A ChoiceCti that allows selecting one of the installed fonts families with a QFontCombobox

        The configValues are determined automatically, they cannot be set in the constructor.

        The QFontCombobox is not editable. I could get it to work well with the FontCti and
        automatic determination of the configValue. It doesn't add much anyway IHMO.
    """
    def __init__(self, nodeName, defaultFamily='Helvetica'):
        """ Constructor.

            :param defaultFamily: A string representing the defaultValue.
            :editable: True if the underlying QFontComboBox is editable. The default is False as
                it does not work well with the FontCti.

            For the (other) parameters see the AbstractCti constructor documentation.
        """
        check_is_a_string(defaultFamily)

        # Get a list of of configValues by reading them from a temporary QFontComboBox.
        tempFontComboBox = QtWidgets.QFontComboBox()
        configValues = []
        defaultData = 0
        for idx in range(tempFontComboBox.count()):
            fontFamily = tempFontComboBox.itemText(idx)
            configValues.append(fontFamily)
            if fontFamily.lower() == defaultFamily.lower():
                defaultData = idx

        # Set after self._displayValues are defined. The parent constructor calls _enforceDataType
        super(FontChoiceCti, self).__init__(nodeName, defaultData, configValues=configValues)


    def createEditor(self, delegate, parent, option):
        """ Creates a ChoiceCtiEditor.
            For the parameters see the AbstractCti constructor documentation.
        """
        return FontChoiceCtiEditor(self, delegate, parent=parent)



class FontChoiceCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a QCombobox for editing ChoiceCti objects.
    """
    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters
        """
        super(FontChoiceCtiEditor, self).__init__(cti, delegate, parent=parent)

        comboBox = QtWidgets.QFontComboBox()
        # The QFontCombobox is not editable. because an non-existing value resulted in a QFont()
        # without parameter whose font family was probably some style sheet value. This didn't
        # work well with the extra options of the automatic configValue generation and with the
        # a possible parent FontCti: a non-exisiting family yields a QFont() with a non-existing
        # family, proably a style-sheet name, which I don't know how to handle.
        comboBox.setEditable(False)

        # The current font family is not properly selected when the combobox is created (at least
        # on OS-X). Setting the setMaxVisibleItems didn't help.
        # http://stackoverflow.com/questions/11252299/pyqt-qcombobox-setting-number-of-visible-items-in-dropdown
        # comboBox.setMaxVisibleItems(15)
        # comboBox.setStyleSheet("QComboBox { combobox-popup: 0; }");

        comboBox.activated.connect(self.comboBoxActivated)
        self.comboBox = self.addSubEditor(comboBox, isFocusProxy=True)


    def finalize(self):
        """ Is called when the editor is closed. Disconnect signals.
        """
        self.comboBox.activated.disconnect(self.comboBoxActivated)
        super(FontChoiceCtiEditor, self).finalize()


    def setData(self, data):
        """ Provides the main editor widget with a data to manipulate.
        """
        self.comboBox.setCurrentIndex(data)


    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.comboBox.currentIndex()


    @QtSlot(int)
    def comboBoxActivated(self, index):
        """ Is called when the user chooses an item in the combo box. The item's index is passed.
            Note that this signal is sent even when the choice is not changed.
        """
        self.delegate.commitData.emit(self)



class PenCti(BoolCti):
    """ Config Tree Item to configure a QPen for drawing lines.

        It will create children for the pen color, width and style. It will not create a child
        for the brush.
    """
    def __init__(self, nodeName, defaultData, resetTo=None, expanded=True,
                 includeNoneStyle=False, includeZeroWidth=False):
        """ Sets the children's default value using the resetTo value.

            The resetTo value must be a QPen or value that can be converted to QPen. It is used
            to initialize the child nodes' defaultValues. If resetTo is None, the default QPen
            will be used, which is a black solid pen of width 1.0.

            (resetTo is not called 'defaultData' since the PenCti itself always has a data and
            defaultData of None. That is, it does not store the data itself but relies on its
            child nodes). The default data, is used to indicate if the pen is enabled.

            If includeNonStyle is True, an None-option will be prepended to the style choice
        """
        super(PenCti, self).__init__(nodeName, defaultData, expanded=expanded,
                                     childrenDisabledValue=False)
        # We don't need a similar initFrom parameter.
        qPen = QtGui.QPen(resetTo)

        self.colorCti = self.insertChild(ColorCti('color', defaultData=qPen.color()))
        defaultIndex = PEN_STYLE_CONFIG_VALUES.index(qPen.style()) + int(includeNoneStyle)
        self.styleCti = self.insertChild(createPenStyleCti('style', defaultData=defaultIndex,
                                                           includeNone=includeNoneStyle))
        self.widthCti = self.insertChild(createPenWidthCti('width', defaultData=qPen.widthF(),
                                                zeroValueText=' ' if includeZeroWidth else None))


    @property
    def configValue(self):
        """ Creates a QPen made of the children's config values.
        """
        if not self.data:
            return None
        else:
            pen = QtGui.QPen()
            pen.setCosmetic(True)
            pen.setColor(self.colorCti.configValue)
            style = self.styleCti.configValue
            if style is not None:
                pen.setStyle(style)
            pen.setWidthF(self.widthCti.configValue)
            return pen


    def createPen(self, altStyle=None, altWidth=None):
        """ Creates a pen from the config values with the style overridden by altStyle if the
            None-option is selected in the combo box.
        """
        pen = self.configValue
        if pen is not None:

            style = self.findByNodePath('style').configValue
            if style is None and altStyle is not None:
                pen.setStyle(altStyle)

            width = self.findByNodePath('width').configValue
            if width == 0.0 and altWidth is not None:
                #logger.debug("Setting altWidth = {!r}".format(altWidth))
                pen.setWidthF(altWidth)

        return pen




