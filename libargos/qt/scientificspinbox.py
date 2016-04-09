""" Contains ScientificDoubleSpinBox, a QDoubleSpinBox that can handle scientific notation.

    Gratefully copied and adapted from:
        https://www.jdreaver.com/posts/2014-07-28-scientific-notation-spin-box-pyside.html

    At the moment only scientific notation (%e) is supported, no regular notation (%f). This
    is for simplicity.

"""
from __future__ import division

import re, logging
import numpy as np
from libargos.qt import QtGui

logger = logging.getLogger(__name__)

# Regular expression to find floats. Match groups are the whole string, the
# whole coefficient, the decimal part of the coefficient, and the exponent
# part.
REGEXP_FLOAT = re.compile(r'(([+-]?\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)')

SMALL_STEPS = 10 # 10 small steps (up/down arrow) in large step (page up/down)
STEP_FACTOR = np.power(10.0, 1.0 / SMALL_STEPS)

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
        self.setMinimum(np.finfo('d').min)
        self.setMaximum(np.finfo('d').max)
        self.validator = FloatValidator()
        self.setDecimals(323) # because of the limitations of the double type (see Qt docs).

    def validate(self, text, position):
        return self.validator.validate(text, position)

    def fixup(self, text):
        return self.validator.fixup(text)

    def valueFromText(self, text):
        return float(text)

    def textFromValue(self, value):
        return "{:.{precission}e}".format(value, precission=self.precision)

    def stepBy(self, steps):
        """ Function that is called whenever the user triggers a step. The steps parameter
            indicates how many steps were taken, e.g. Pressing Qt::Key_Down will trigger a call to
            stepBy(-1), whereas pressing Qt::Key_Prior will trigger a call to stepBy(10).
        """
        oldValue = self.value()

        if oldValue == 0:
            return steps

        if steps == 1:
            newValue = self.value() * STEP_FACTOR
        elif steps == -1:
            newValue = self.value() / STEP_FACTOR
        elif steps == 10:
            newValue = self.value() * 10
        elif steps == -10:
            newValue = self.value() / 10
        else:
            raise ValueError("Invalid step size: {!r}, value={}".format(steps, value))

        newValue = float(newValue)

        if newValue < self.minimum():
            newValue = self.minimum()

        if newValue > self.maximum():
            newValue = self.maximum()

        logger.debug("stepBy {}: {} -> {}".format(steps, oldValue, newValue))
        try:
            self.setValue(newValue)
        except:
            logger.warn("Unable to set spinbox to: {!r}".format(newValue))
            self.setValue(oldValue)


    def __old__stepBy(self, steps):
        #text = self.cleanText()
        text = "{:.17}".format(self.value())
        groups = REGEXP_FLOAT.search(text).groups()
        mantissa = float(groups[1])
        mantissa += steps
        new_string = "{:.{precission}f}".format(mantissa, precission=self.precision) + (groups[3] if groups[3] else "")
        self.lineEdit().setText(new_string)


if __name__ == "__main__":
    import sys

    def main():
        """ Small stand-alone test
        """
        app = QtGui.QApplication(sys.argv[1:])
        win = ScientificDoubleSpinBox()
        win.raise_()
        win.show()
        sys.exit(app.exec_())


    #######
    main()