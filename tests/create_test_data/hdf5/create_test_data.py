#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Create some data files that can be used for testing.

    Is by no means extensive perhaps in the future it will.
    For now, it is updated when issues are encountered.
"""
import enum
import logging
import os.path

import numpy as np

from argos.utils.dirs import ensureDirectoryExists
from argos.utils.logs import makeLogFormat

logger = logging.getLogger("create_test_data")

def createEnum():
    """ Create test file with enumeration type.

        See: https://docs.h5py.org/en/stable/special.html#enumerated-types
    """
    import h5py

    dt = h5py.enum_dtype({"RED": 0, "GREEN": 1, "BLUE": 2}, basetype=np.uint16)
    h5py.check_enum_dtype(dt)  # {'BLUE': 3, 'GREEN': 1, 'RED': 0}

    with h5py.File('enums.h5', 'w') as h5Root:
        h5Root.create_dataset("colors", data=np.arange(5), dtype=dt)
        h5Root.create_dataset("color", data=1, dtype=dt)



def readEnum():
    """ Reads the file with enums and creates object array with enums
    """
    import h5py
    with h5py.File('enums.h5', 'r') as h5Root:
        ds = h5Root["colors"]
        dt = ds.dtype
        dct = h5py.check_enum_dtype(dt)
        assert dct, "dict is empty"

        EnumCls = enum.IntEnum('EnumCls', dct)

        def safeCreateEnum(v):
            """ Creates EnumCls if v in the values. Otherwise returns v"""
            try:
                return EnumCls(v)
            except ValueError:
                return v

        VecEnumCls = np.vectorize(safeCreateEnum, otypes=[EnumCls])

        data = VecEnumCls(ds[:])
        logger.info("Enum object array: {}".format(data))


def createHdfEmpty():
    """ Create test file with empty datasets and attributes.
    """
    import h5py

    # Emtpy datasets
    # See https://docs.h5py.org/en/latest/high/dataset.html#creating-and-reading-empty-or-null-datasets-and-attributes
    # and https://github.com/h5py/h5py/issues/279#issuecomment-15313062 for a possible use case
    with h5py.File('empty.h5', 'w') as h5Root:
        ds = h5Root.create_dataset("emptyDataset", data=h5py.Empty("f"))
        ds.attrs['Description'] = 'An empty dataset'

        # Broken in 2.10 but was fixed in 3.0 https://github.com/h5py/h5py/issues/1540
        ds = h5Root.create_dataset("hasEmptyAttribute", data=np.arange(5))
        ds.attrs['Description'] = 'An regular dataset with an empty attribute'
        ds.attrs["emptyAttr"] = h5py.Empty(np.float32)


def createHdfDims():
    """ Create test file with various dimensions and scales.
    """
    import h5py

    with h5py.File('dimensions.h5', 'w') as h5Root:

        dsTime = h5Root.create_dataset("tine", shape=(3, ), data=np.arange(3))
        dsTime.dims[0].label = 'time'
        dsTime.make_scale()

        dsRow = h5Root.create_dataset("row", shape=(4, ), data=np.arange(4))
        dsRow.make_scale(name="name-row")

        dsCol = h5Root.create_dataset("col", shape=(5, ), data=np.arange(5))
        dsCol.make_scale(name="name-col")

        data = np.arange(60).reshape((3, 4, 5))
        logger.debug(f"data shape: {data.shape}")

        dsCube = h5Root.create_dataset("data_cube", data=data)
        dsCube.dims[0].attach_scale(dsTime)
        dsCube.dims[1].attach_scale(dsRow)

        dsCube.dims[2].attach_scale(dsCol)
        dsCube.dims[2].label = 'label-col'


def createHdfSubArray():
    """ Create test file with structured arrays where fields are arrays in itself.
        Forked also ``createArgosTestData``, which creates the same arrays in memory.
    """
    import h5py

    with h5py.File('sub_arrays.h5', 'w') as h5Root:

        h5Root.create_dataset('structured_arr1',
            data=np.array([(1, 2., 'Hello'), (2, 3., "World")],
                          dtype=[('foo', 'i4'), ('bar', 'f4'), ('baz', 'S10')] ))

        h5Root.create_dataset('structured_arr2',
            data=np.array([(1.5,2.5,(1.0,2.0)),(3.,4.,(4.,5.)),(1.,3.,(2.,6.))],
                          dtype=[('x','f4'),('y',np.float32),('value','f4',(2,2))] ))

        h5Root.create_dataset('structured_arr3',
            data=np.array([(1.5,2.5,[2.0, -1.0]),(3.,4.,[5., 88]),(1.,3.,[2., 0.01])],
                          dtype=[('1st','f4'),('2nd',np.float32),('3rd','f4',(2,))] ))

        # A structured array with offsets and titles
        dt4 = np.dtype({'names': ['r', 'b'], 'formats': ['u1', 'u1'], 'offsets': [0, 2]})
        h5Root.create_dataset('structured_arr4',
            data=np.array([(255, 11), (1, 50)], dtype=dt4 ))

        # Nested structured array
        dt5 = [('year', '<i4'), ('countries', [('c1', [('iso','a3'), ('my_value','<f4')]),
                                               ('c2', [('iso','a3'), ('your_value','<f8', (3,))])])]
        h5Root.create_dataset('structured_arr5',
            data=np.array([(2009, (('USA', 10.0), ('CHN', [-16.9, 0, 1000]))),
                           (2010, (('BRA', 11.2), ('ARG', [12.0, 17.2, np.nan])))], dtype=dt5))


def createTestData(outputDir):
    """ Creates test data files in output directory
    """
    logger.info("Changing output dir to: {}".format(os.path.abspath(outputDir)))
    ensureDirectoryExists(outputDir)
    oldDir = os.getcwd()
    os.chdir(outputDir)
    try:
        createEnum()
        readEnum()
        createHdfEmpty()
        createHdfDims()
        createHdfSubArray()
    finally:
        logger.info("Changing output dir back to: {}".format(os.path.abspath(oldDir)))
        os.chdir(oldDir)




if __name__ == "__main__":
    logging.basicConfig(level="DEBUG", format=makeLogFormat(loggerName=True, fileLine=False))
    createTestData("test_data")
