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

from libargos.config.abstractcti import AbstractCti, AbstractCtiEditor, InvalidInputError
from libargos.config.boolcti import BoolCti
from libargos.config.choicecti import ChoiceCti
from libargos.config.floatcti import FloatCti


from libargos.qt import Qt, QtCore, QtGui
from libargos.utils.misc import NOT_SPECIFIED

logger = logging.getLogger(__name__)
          

PEN_STYLE_DISPLAY_VALUES = ('solid', 'dashed', 'dotted', 'dash-dot', 'dash-dot-dot')
PEN_STYLE_CONFIG_VALUES = (Qt.SolidLine, Qt.DashLine, Qt.DotLine, 
                           Qt.DashDotLine, Qt.DashDotDotLine)


def createPenStyleCti(nodeName, data=NOT_SPECIFIED, defaultData=0, includeNone=False):
    """ Creates a ChoiceCti with Qt PenStyles.
        If includeEmtpy is True, the first option will be None.
    """
    displayValues=PEN_STYLE_DISPLAY_VALUES
    configValues=PEN_STYLE_CONFIG_VALUES
    if includeNone:
        displayValues = [''] + list(displayValues)
        configValues = [None] + list(configValues)
    return ChoiceCti(nodeName, data=data, defaultData=defaultData, 
                     displayValues=displayValues, configValues=configValues)

             
def createPenWidthCti(nodeName, defaultData=1.0, zeroValueText=None):
    """ Creates a FloatCti with defaults for configuring a QPen width.
    
        If specialValueZero is set, this string will be displayed when 0.0 is selected.
        If specialValueZero is None, the minValue will be 0.1
    """
    # A pen line width of zero indicates a cosmetic pen. This means that the pen width is 
    # always drawn one pixel wide, independent of the transformation set on the painter.
    # Note that line widths other than 1 may be slow when anti aliasing is on.
    return FloatCti('width', defaultData=defaultData, specialValueText=zeroValueText, 
                    minValue=0.1 if zeroValueText is None else 0.0, 
                    maxValue=100, stepSize=0.1, decimals=1)
        
   
class ColorCti(AbstractCti):
    """ Config Tree Item to store a color. 
    """
    def __init__(self, nodeName, data=NOT_SPECIFIED, defaultData=''):
        """ Constructor. 
            For the (other) parameters see the AbstractCti constructor documentation.
        """
        super(ColorCti, self).__init__(nodeName, data=data, defaultData=defaultData)

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
        """ Returns the data (QColor) as to be displayed as decoration
        """
        return self.data
    
    def _dataToJson(self, qColor):
        """ Converts data or defaultData to serializable json dictionary or scalar.
            Helper function that can be overridden; by default the input is returned.
        """
        return qColor.name()
    
    def _dataFromJson(self, json):
        """ Converts json dictionary or scalar to an object to use in self.data or defaultData.
            Helper function that can be overridden; by default the input is returned.
        """
        return QtGui.QColor(json) 
        
    
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
        
        lineEditor = QtGui.QLineEdit(parent)
        regExp = QtCore.QRegExp(r'#?[0-9A-F]{6}', Qt.CaseInsensitive)
        validator = QtGui.QRegExpValidator(regExp, parent=lineEditor)
        lineEditor.setValidator(validator)
        
        self.lineEditor = self.addSubEditor(lineEditor, isFocusProxy=True)
        
        pickButton = QtGui.QToolButton()
        pickButton.setText("...")
        pickButton.setToolTip("Open color dialog.")
        #pickButton.setIcon(QtGui.QIcon(os.path.join(icons_directory(), 'err.warning.svg')))
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
        
        qColor = QtGui.QColorDialog.getColor(currentColor, self)
        
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


             
class PenCti(BoolCti):
    """ Config Tree Item to configure a QPen for drawing lines. 
    
        It will create children for the pen color, width and style. It will not create a child
        for the brush.
    """
    def __init__(self, nodeName, resetTo=None, includeNoneStyle=False, includeZeroWidth=False):
        """ Sets the children's default value using the resetTo value.
        
            The resetTo value must be a QPen or value that can be converted to QPen. It is used
            to initialize the child nodes' defaultValues. If resetTo is None, the default QPen
            will be used, which is a black solid pen of width 1.0.
            
            (resetTo is not called 'defaultData' since the PenCti itself always has a data and 
            defaultData of None. That is, it does not store the data itself but relies on its 
            child nodes).
            
            If includeNonStyle is True, an None-option will be prepended to the style choice
        """
        super(PenCti, self).__init__(nodeName)
        # We don't need a similar initFrom parameter.
        qPen = QtGui.QPen(resetTo)
        
        self.insertChild(ColorCti('color', defaultData=qPen.color()))
        defaultIndex = PEN_STYLE_CONFIG_VALUES.index(qPen.style()) + int(includeNoneStyle)
        self.insertChild(createPenStyleCti('style', defaultData=defaultIndex, 
                                           includeNone=includeNoneStyle))
        self.insertChild(createPenWidthCti('width', defaultData=qPen.widthF(), 
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
            pen.setColor(self.findByNodePath('color').configValue)
            style = self.findByNodePath('style').configValue
            if style is not None:
                pen.setStyle(self.findByNodePath('style').configValue)
            pen.setWidthF(self.findByNodePath('width').configValue)
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
                logger.debug("Setting altWidth = {!r}".format(altWidth))
                pen.setWidthF(altWidth)
                 
        return pen
    


    