""" Contains ScientificDoubleSpinBox, a QDoubleSpinBox that can handle scientific notation.

    Gratefully copied and adapted from:
        https://www.jdreaver.com/posts/2014-07-28-scientific-notation-spin-box-pyside.html

"""
from __future__ import division

import re, logging
import numpy as np
from argos.qt import QtGui, QtWidgets

logger = logging.getLogger(__name__)

# Regular expression to find floats. Match groups are the whole string, the
# whole coefficient, the decimal part of the coefficient, and the exponent
# part.
REGEXP_FLOAT = re.compile(r'(([+-]?\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)')


def format_float(value): # not used
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



class ScientificDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    """ A QDoubleSpinBox that can handle scientific notation.
    """
    def __init__(self,
                 precision=6,
                 largeStepFactor=10,
                 smallStepsPerLargeStep=10,
                 *args, **kwargs):
        """ Constructor.

            In contrast to the QDoubleSpinbox the (page)up/down let the value grow exponentially.
            That is, the spinbox value is multiplied by a small step factor when the up-arrow is
            pressed, and by a larger factor if page-up is pressed. A large step multiplies the value
            spinbox value with largeStepFactor (default 10). The smallStepsPerLargeStep does then
            specify how many up-arrow key presses are needed to increase to largeStepFactor.

            :param precision: The precision used in the scientific notation.
            :param largeStepFactor: default 10
            :param smallStepsPerLargeStep: default 10
        """
        self.precision = precision
        super(ScientificDoubleSpinBox, self).__init__(*args, **kwargs)
        self.setMinimum(np.finfo('d').min)
        self.setMaximum(np.finfo('d').max)
        self.validator = FloatValidator()
        self.setDecimals(323) # because of the limitations of the double type (see Qt docs).

        self._smallStepFactor = None # determined by _smallStepsPerLargeStep and _largeStepFactor
        self._smallStepsPerLargeStep = None
        self._largeStepFactor = largeStepFactor
        self.smallStepsPerLargeStep = smallStepsPerLargeStep


    def validate(self, text, position):
        result = self.validator.validate(text, position)
        #logger.debug("validate result: {}".format(result))
        return result


    def fixup(self, text):
        result = self.validator.fixup(text)
        #logger.debug("fixup: {}".format(result))
        return result


    def valueFromText(self, text):
        return float(text)


    def textFromValue(self, value):
        return "{:.{precission}g}".format(value, precission=self.precision)


    @property
    def largeStepFactor(self):
        """ The spinbox will be multiplied with this factor whenever page up is pressed.
        """
        return self._largeStepFactor


    @largeStepFactor.setter
    def largeStepFactor(self, largeStepFactor):
        """ The spinbox will be multiplied with this factor whenever page up is pressed.
        """
        self._largeStepFactor = largeStepFactor


    @property
    def smallStepFactor(self):
        """ The spinbox will be multiplied with this factor whenever page up is pressed.
            Read-only property. Setting is done via largeStepFactor and smallStepsPerLargeStep.
        """
        return self._smallStepFactor


    @property
    def smallStepsPerLargeStep(self):
        """ The number of small steps that go in a large one.

            The spinbox value is increased with a small step when the up-arrow is pressed, and by
            a large step if page-up is pressed. A large step increases the value increases the
            spinbox value with largeStepFactor (default 10). The smallStepsPerLargeStep does then
            specify how many up-arrow key presses are needed to increase to largeStepFactor.
        """
        return self._smallStepsPerLargeStep


    @smallStepsPerLargeStep.setter
    def smallStepsPerLargeStep(self, smallStepsPerLargeStep):
        """ Sets the number of small steps that go in a large one.

        """
        self._smallStepsPerLargeStep = smallStepsPerLargeStep
        self._smallStepFactor = np.power(self.largeStepFactor, 1.0 / smallStepsPerLargeStep)


    def stepBy(self, steps):
        """ Function that is called whenever the user triggers a step. The steps parameter
            indicates how many steps were taken, e.g. Pressing Qt::Key_Down will trigger a call to
            stepBy(-1), whereas pressing Qt::Key_Prior will trigger a call to stepBy(10).
        """
        oldValue = self.value()

        if oldValue == 0:
            newValue = steps
        elif steps == 1:
            newValue = self.value() * self.smallStepFactor
        elif steps == -1:
            newValue = self.value() / self.smallStepFactor
        elif steps == 10:
            newValue = self.value() * self.largeStepFactor
        elif steps == -10:
            newValue = self.value() / self.largeStepFactor
        else:
            raise ValueError("Invalid step size: {!r}, value={}".format(steps, oldValue))

        newValue = float(newValue)

        if newValue < self.minimum():
            newValue = self.minimum()

        if newValue > self.maximum():
            newValue = self.maximum()

        #logger.debug("stepBy {}: {} -> {}".format(steps, oldValue, newValue))
        try:
            self.setValue(newValue)
        except Exception:
            # TODO: does this ever happen? Better validation (e.g. catch underflows)
            logger.warn("Unable to set spinbox to: {!r}".format(newValue))
            self.setValue(oldValue)



if __name__ == "__main__":
    import sys

    logger = logging.getLogger(__name__)
    logging.basicConfig(level='DEBUG', stream=sys.stderr,
        format='%(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-7s: %(message)s')

    def main():
        """ Small stand-alone test
        """
        app = QtWidgets.QApplication(sys.argv[1:])
        spinBox = ScientificDoubleSpinBox(precision = 9, largeStepFactor=2, smallStepsPerLargeStep=3)
        spinBox.selectAll()
        spinBox.setSingleStep(2)
        spinBox.raise_()
        spinBox.show()
        sys.exit(app.exec_())


    #######
    main()
