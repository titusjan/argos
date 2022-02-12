""" Program to test if PyQt 5.12 can work with Python 3.10

Python 3.10, PyQt 5.12 -> flags: <PyQt5.QtCore.Qt.ItemFlags object at 0x116804b30>
Python 3.10, PyQt 5.15 -> flags: <PyQt5.QtCore.Qt.ItemFlags object at 0x109be95b0>

"""
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QT_VERSION_STR
from PyQt5.Qt import PYQT_VERSION_STR

print("Python version: {}".format(sys.version))
print("Qt version: {}".format(QT_VERSION_STR))
print("PyQt version: {}".format(PYQT_VERSION_STR))
print()

a = Qt.NoItemFlags | Qt.ItemIsEnabled
b = Qt.ItemIsTristate | Qt.ItemIsUserCheckable

print(a|b)








