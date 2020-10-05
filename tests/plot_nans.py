""" NaNs not plotted

    https://github.com/pyqtgraph/pyqtgraph/issues/1057

Also
    https://github.com/pyqtgraph/pyqtgraph/issues/1011


"""

import numpy as np
import pyqtgraph as pg

print("Qt Version: {}".format(pg.QtCore.QT_VERSION_STR))
print("PyQt Version: {}".format(pg.QtCore.PYQT_VERSION_STR))

data = np.random.normal(size=20)
data2 = np.random.normal(size=20)
data2 = data2.astype(np.float32)
print("data2.dtype: {}".format(data2.dtype))
#data2[0] = np.nan

data2[10] = 1e14 # Works

data2[10] = 4.17e14 # still works
# data2[10] = 4.18e14 # Fails

#data2[10] = 2e27
data2[15] = np.nan


#data2[100] = 4.5e14 # See pyqtgraph issue #1011

#pg.plot(data, title="no NaN")
pg.plot(data2, title="one NaN")

pg.QtGui.QApplication.exec_()
