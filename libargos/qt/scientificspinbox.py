""" Contains ScientificDoubleSpinBox, a QDoubleSpinBox that can handle scientific notation.

    Greatefully copied and adapted from:
        https://www.jdreaver.com/posts/2014-07-28-scientific-notation-spin-box-pyside.html

"""

import re, logging
import numpy as np
from libargos.qt import QtGui

logger = logging.getLogger(__name__)

# Regular expression to find floats. Match groups are the whole string, the
# whole coefficient, the decimal part of the coefficient, and the exponent
# part.
REGEXP_FLOAT = re.compile(r'(([+-]?\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)')


def format_float(value):
    """Modified form of the 'g' format specifier.
    """
    string = "{:g}".format(value).replace("e+", "e")
    string = re.sub("e(-?)0*(\d+)", r"e\1\2", string)
    return string


def valid_float_string(string):
    match = REGEXP_FLOAT.search(string)
    return match.groups()[0] == string if match else False


class FloatValidator(QtGui.QValidator):

    def validate(self, string, position):
        if valid_float_string(string):
            return (QtGui.QValidator.Acceptable, string, position)
        if string == "" or string[position-1] in 'e.-+':
            return (QtGui.QValidator.Intermediate, string, position)
        return (QtGui.QValidator.Invalid , string, position)

    def fixup(self, text):
        match = REGEXP_FLOAT.search(text)
        return match.groups()[0] if match else ""


class ScientificDoubleSpinBox(QtGui.QDoubleSpinBox):
    """ A QDoubleSpinBox that can handle scientific notation.
    """
    def __init__(self, precision=6, *args, **kwargs):
        self.precision = precision
        super(ScientificDoubleSpinBox, self).__init__(*args, **kwargs)
        self.setMinimum(-np.inf)
        self.setMaximum(np.inf)
        self.validator = FloatValidator()
        self.setDecimals(1000)

    def validate(self, text, position):
        return self.validator.validate(text, position)

    def fixup(self, text):
        return self.validator.fixup(text)

    def valueFromText(self, text):
        return float(text)

    def textFromValue(self, value):
        return format_float(value)

    def stepBy(self, steps):
        text = self.cleanText()
        groups = REGEXP_FLOAT.search(text).groups()
        decimal = float(groups[1])
        decimal += steps
        new_string = "{:g}".format(decimal) + (groups[3] if groups[3] else "")
        self.lineEdit().setText(new_string)

