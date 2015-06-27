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
from libargos.config.choicecti import ChoiceCti
from libargos.config.floatcti import FloatCti
from libargos.config.emptycti import EmptyCti, EmptyCtiEditor


from libargos.qt import Qt, QtCore, QtGui
from libargos.utils.misc import NOT_SPECIFIED

logger = logging.getLogger(__name__)
          


def createPenStyleCti(nodeName, data=NOT_SPECIFIED, defaultData=0):
    """ Creates a ChoiceCti with Qt PenStyles
    """
    return ChoiceCti(nodeName, data=data, defaultData=defaultData, 
                     displayValues=['solid line', 'dashed line', 'dotted line', 
                                    'dash-dot line', 'dash-dot-dot line'], 
                     configValues=[Qt.SolidLine, Qt.DashLine, Qt.DotLine, 
                                   Qt.DashDotLine, Qt.DashDotDotLine])

   
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

             
             
class PenCti(EmptyCti):
    """ Config Tree Item to configure a QPen for drawing lines. 
    
        It will create children for the pen color, width and style. It will not create a child
        for the brush.
    """
    def __init__(self, nodeName):
        """ Constructor. 
            For the (other) parameters see the AbstractCti constructor documentation.
        """
        super(PenCti, self).__init__(nodeName)
        
        self.insertChild(ColorCti('color', defaultData='#000000'))
        
        # A pen line width of zero indicates a cosmetic pen. This means that the pen width is 
        # always drawn one pixel wide, independent of the transformation set on the painter.
        # Note that line widths other than 1 may be slow when anti aliasing is on.
        self.insertChild(FloatCti('width', defaultData=1.0, 
                                  minValue=0.0, maxValue=100, stepSize=1, decimals=1))
        
        self.insertChild(createPenStyleCti('style'))
        
        
    @property
    def configValue(self):
        """ A QPen made of the children's config values
        """        
        pen = QtGui.QPen()
        pen.setCosmetic(True)
        pen.setColor(self.findByNodePath('color').configValue)
        pen.setWidthF(self.findByNodePath('width').configValue)
        pen.setStyle(self.findByNodePath('style').configValue)

        return pen

    
        
    def _dataToString(self, qPen):
        """ Conversion function used to convert the (default)data to the display value.
        """
        return "Color: {}, width={})".format(qPen.color().name().upper(), qPen.width())
        
    
    