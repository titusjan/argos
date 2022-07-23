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

from __future__ import division, print_function

import logging
import warnings

import numpy as np
import numpy.ma as ma

from decimal import Decimal
from argos.repo.memoryrtis import MappingRti, SyntheticArrayRti
from argos.repo.registry import ICON_COLOR_MEMORY, ICON_COLOR_PANDAS
from argos.utils.moduleinfo import versionStrToTuple


logger = logging.getLogger(__name__)

# the size of the colormap test images
SIZE_X = 500
SIZE_Y = 500

def makeConcentricCircles():
    """ Creates concentric cricle pattern.

        :return: 2D numpy array
    """
    x = np.linspace(-10, 10, num=SIZE_X)
    y = np.linspace(-10, 10, num=SIZE_Y)
    xx, yy = np.meshgrid(x, y, sparse=False)
    z = np.sin(xx**2 + yy**2) / (xx**2 + yy**2)
    return z


def makeRamp():
    """ Create 'ramp' function from Peter Karpov's blog http://inversed.ru/Blog_2.htm

        Slightly modified version of the test function introduced by Peter Kovesi
        Good Colour Maps: How to Design Them. Peter Kovesi, arxiv.org, 2015.
        http://arxiv.org/abs/1509.03700

        Allows to visually assess perceptual uniformity by observing the distance at which the sine \
        pattern fades.

        :return: 2D numpy array
    """
    x = np.linspace(0, 1, num=SIZE_X)
    y = np.linspace(0, 1, num=SIZE_Y)
    xx, yy = np.meshgrid(x, y, sparse=False)
    #z = yy + xx**2  # demonstrates banding
    z = yy + (xx**2) * np.sin(64 * 2 * np.pi * yy) / 12
    # z = np.clip(z, 0.0, 1.0) # Fails in PyQtGraph 2D plot :-/
    return z


def makeArcTan2():
    """ Create atan2(x, y), which is goog for testing circular color maps.
        :return: 2D numpy array
    """
    x = np.linspace(-1, 1, num=SIZE_X)
    y = np.linspace(-1, 1, num=SIZE_Y)
    xx, yy = np.meshgrid(x, y, sparse=False)
    return np.arctan2(xx, yy)


def makeSpiral():
    """ Create 'spiral' function from Peter Karpov's blog http://inversed.ru/Blog_2.htm

        Smoothness test, has a near-uniform distribution of values.
        :return: 2D numpy array
    """
    x = np.linspace(-1, 1, num=SIZE_X)
    y = np.linspace(-1, 1, num=SIZE_Y)
    xx, yy = np.meshgrid(x, y, sparse=False)
    return np.arcsin(np.sin(2 * 2 * np.pi * (xx**2 + yy**2) + np.arctan2(xx, yy)))


def makeSineProduct():
    """ Create 'two sines products' function from Peter Karpov's blog http://inversed.ru/Blog_2.htm

        Smoothness test.
        :return: 2D numpy array
    """
    x = np.linspace(-np.pi, np.pi, num=SIZE_X)
    y = np.linspace(-np.pi, np.pi, num=SIZE_Y)
    xx, yy = np.meshgrid(x, y, sparse=False)
    return np.sin(xx) * np.sin(yy) + np.sin(3*xx) * np.sin(3*yy)


def makeUniformNoise():
    """ Uniform noise between 0 and 1
    """
    return np.random.uniform(0.0, 1.0, size=(400, 300))


def createArgosTestData():
    """ Makes various test data sets for debugging
    """
    myDict = {}
    myDict['name'] = 'Pac Man'
    myDict['age'] = 34
    myDict['ghosts'] = ['Inky', 'Blinky', 'Pinky', 'Clyde']
    myDict['none'] = None
    myDict['numbers'] = {'int': 5, 'float': -6.6, 'large float': 7e77,
                         '-inf': np.NINF, 'nan': np.nan, 'complex': 8-9j, 'decimal': Decimal(4.444)}

    myDict['random'] = np.random.randn(8, 5)
    array = np.arange(240, dtype=np.float64).reshape(8, 30).transpose()
    #array[10, 4] = 7e77
    myDict['array'] = array

    myDict['ones'] = np.ones_like(array)

    x = np.arange(60)
    parabola = 0.02 * np.square(x)
    myDict['parabola'] = parabola

    myDict['array_1K'] = np.random.randn(1000)
    myDict['array_10K'] = np.random.randn(10 * 1000)
    myDict['array_100K'] = np.random.randn(100 * 1000)
    myDict['array_200K'] = np.random.randn(200 * 1000)
    myDict['array_500K'] = np.random.randn(500 * 1000)
    myDict['array_1000K'] = np.random.randn(1000 * 1000)

    #masked_array = ma.arange(2400, dtype=np.float16).reshape(60, 40)
    masked_array = np.transpose(ma.ones(shape=(40, 60)) * parabola)
    masked_array[:, 0:7] = ma.masked
    masked_array[15:45, 10:17] = ma.masked
    myDict['array_masked'] = masked_array

    nan_array = np.arange(2400, dtype=np.float16).reshape(60, 40)
    nan_array[:, 0:7] = np.nan
    nan_array[15:45, 10:17] = np.nan
    myDict['array_with_nans'] = nan_array

    inf_array = np.arange(2400, dtype=np.float16).reshape(60, 40)
    inf_array[:, 0:7] = np.inf
    inf_array[15:45, 10:17] = np.NINF
    myDict['array_with_infs'] = inf_array

    myDict['empty_array1D'] = np.ones(shape=(0, ))
    myDict['empty_array2D'] = np.ones(shape=(0, 6))
    myDict['empty_array3D'] = np.ones(shape=(10, 0, 6))

    myDict['structured_arr1'] = np.array([(1,2.,'Hello'), (2,3.,"World")],
                                          dtype=[('foo', 'i4'),('bar', 'f4'), ('baz', 'S10')])

    myDict['structured_arr2'] = np.array([(1.5,2.5,(1.0,2.0)),(3.,4.,(4.,5.)),(1.,3.,(2.,6.))],
                                         dtype=[('x','f4'),('y',np.float32),('value','f4',(2,2))])
    myDict['structured_arr3'] = np.array([(1.5,2.5,[2.0, -1.0]),(3.,4.,[5., 88]),(1.,3.,[2., 0.01])],
                                         dtype=[('1st','f4'),('2nd',np.float32),('3rd','f4',(2,))])

    # A structured array with offsets and titles
    dt4 = np.dtype({'names': ['r','b'], 'formats': ['u1', 'u1'], 'offsets': [0, 2]})
                    #'titles': ['Red pixel', 'Blue pixel']})
    myDict['structured_arr4'] = np.array([(255, 11), (1, 50)], dtype=dt4)

    # Nested structured array
    dt5 = [('year', '<i4'), ('countries', [('c1', [('iso','a3'), ('my_value','<f4')]),
                                           ('c2', [('iso','a3'), ('your_value','<f8', (3,))])])]
    myDict['structured_arr5'] = np.array([(2009, (('USA', 10.0), ('CHN', [-16.9, 0, 1000]))),
                                          (2010, (('BRA', 11.2), ('ARG', [12.0, 17.2, np.nan])))],
                                         dtype=dt5)

    # The _structured_masked_arr2 array fails for the Text inspector. Start with '_' to skip test.
    myDict['_structured_masked_arr2'] = ma.MaskedArray(myDict['structured_arr2'], fill_value=-99999)
    myDict['_structured_masked_arr2'].mask[0][0] = True
    myDict['_structured_masked_arr2'].mask[0][2][0,1] = True # doesn't seem to work

    myDict['numpy string array']  = np.array(['Yackity', 'Smackity'])
    myDict['numpy unicode array'] = np.array(['Table', u'ταБЬℓσ'])
    myDict['byte array'] = bytearray(range(256))
    myDict['bytes'] = bytes(bytearray(range(0, 256)))
    myDict['string'] = "The quick brown fox jumps over the lazy dog!"

    mappingRti = MappingRti(myDict, nodeName="myDict", iconColor=ICON_COLOR_MEMORY)

    # If set, the data below is added directly to the MappingRti instead to the underlying
    # dictionary. However, when you open and close the RTI in the tree, this data is lost.
    # Therefore, we turn it off for now and perhaps solve this problem later.
    includeVolatileData = False

    if includeVolatileData:
        # New axis at the beginning and end.
        mappingRti.insertChild(SyntheticArrayRti(
            'newaxis heading 2D', fun=lambda: makeConcentricCircles()[np.newaxis, np.newaxis, ...]))
        mappingRti.insertChild(SyntheticArrayRti(
            'newaxis trailing 2D', fun=lambda: makeConcentricCircles()[..., np.newaxis, np.newaxis]))

        mappingRti.insertChild(SyntheticArrayRti(
            'newaxis heading 1D', fun=lambda: makeConcentricCircles()[50,:][np.newaxis, np.newaxis, :]))

        mappingRti.insertChild(SyntheticArrayRti(
            'newaxis trailing 1D', fun=lambda: makeConcentricCircles()[50,:][:, np.newaxis, np.newaxis]))

        # Synthetic images for testing color maps.
        colorMapRti = mappingRti.insertChild(MappingRti({}, nodeName="test color maps"))
        colorMapRti.insertChild(SyntheticArrayRti('concentric circles', fun=makeConcentricCircles))
        colorMapRti.insertChild(SyntheticArrayRti('ramp', fun=makeRamp))
        colorMapRti.insertChild(SyntheticArrayRti('arctan2', fun=makeArcTan2))
        colorMapRti.insertChild(SyntheticArrayRti('spiral', fun=makeSpiral))
        colorMapRti.insertChild(SyntheticArrayRti('sine product', fun=makeSineProduct))
        colorMapRti.insertChild(SyntheticArrayRti('uniform noise', fun=makeUniformNoise))

        addPandasTestData(mappingRti)

    return mappingRti


def addPandasTestData(rti):
    """ Add some Pandas child RTIs to the rti
    """
    try:
        import pandas as pd
        from argos.repo.rtiplugins.pandasio import (PandasSeriesRti, PandasDataFrameRti,
                                                    PandasPanelRti)
    except ImportError as ex:
        logger.warning("No pandas test data created: {}".format(ex))
        return

    versionInfo = versionStrToTuple(pd.__version__)

    pandsRti = rti.insertChild(MappingRti({}, nodeName="_pandas"))  # for now skip in tests

    s = pd.Series([1, 2, 3, -4, 5], index=list('abcde'), name='simple series')
    pandsRti.insertChild(PandasSeriesRti(s, s.name, iconColor=ICON_COLOR_PANDAS))


    df = pd.DataFrame({'A' : ['foo', 'bar', 'foo', 'bar', 'foo', 'bar', 'foo', 'foo'],
                       'B' : ['one', 'one', 'two', 'three', 'two', 'two', 'one', 'three'],
                       'C' : np.random.randn(8),
                       'D' : np.random.randn(8)})

    pandsRti.insertChild(PandasDataFrameRti(df, 'df', iconColor=ICON_COLOR_PANDAS))

    # Multi index
    arrays = [['bar', 'bar', 'baz', 'baz', 'foo', 'foo', 'qux', 'qux'],
              ['one', 'two', 'one', 'two', 'one', 'two', 'one', 'two']]
    tuples = list(zip(*arrays))
    index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second'])
    s = pd.Series(np.random.randn(8), index=index)
    pandsRti.insertChild(PandasSeriesRti(s, "multi-index", iconColor=ICON_COLOR_PANDAS))
