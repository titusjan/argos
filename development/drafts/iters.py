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

import logging

from argos.qt import QtCore, QtWidgets, Qt, QtSignal

logger = logging.getLogger(__name__)

class Runner(QtCore.QObject):

    sigNextValue = QtSignal(object)  # When a new value is retrieved

    def __init__(self):
        super().__init__()
        self._iterator = None

        self._timer = QtCore.QTimer()
        self._timer.setInterval(0)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._doStep, type=Qt.QueuedConnection)


    def walkIterator(self, iterator):
        assert self._iterator is None, "Already walking an iterator"
        self._iterator = iterator
        self._doStep()


    def _doStep(self):

        try:
            res = next(self._iterator)
            logger.debug("Result: {}".format(res))
            self.sigNextValue.emit(res)
        except StopIteration as ex:
            logger.debug("Stop iteration")
            self._iterator = None
        else:
            self._timer.start()



class MyWindow(QtWidgets.QWidget):
    """ Test window
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._runner = Runner()
        self._runner.sigNextValue.connect(self._setProgressFraction)

        self.mainLayout = QtWidgets.QVBoxLayout(self)

        self.button = QtWidgets.QPushButton("Push me")
        self.mainLayout.addWidget(self.button)
        self.button.clicked.connect(self.onClicked)

        self.progressBar = QtWidgets.QProgressBar()
        self.mainLayout.addWidget(self.progressBar)



    def _setProgressFraction(self, fraction: float):
        """ Sets the fraction (percentage / 100)
        """
        self.progressBar.setValue(int(round(fraction * 100)))
        logger.debug("Progress fraction {:8.3f}".format(fraction))
        #processEvents()


    def onClicked(self):
        logger.debug("Button clicked")
        iterator = (i  / 1000 for i in range(1000))
        self._runner.walkIterator(iterator)



def main():
    app = QtWidgets.QApplication([])
    win = MyWindow()
    win.show()
    win.raise_()
    app.exec()


if __name__ == "__main__":
    main()


