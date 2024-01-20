#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Create some data files that can be used for testing.

    Is by no means extensive perhaps in the future it will.
    For now, it is updated when issues are encountered.
"""
import logging
import os.path

import numpy as np

from argos.utils.dirs import ensureDirectoryExists
from argos.utils.logs import makeLogFormat

logger = logging.getLogger("create_test_data")

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



def createTestData(outputDir):
    """ Creates test data files in output directory
    """
    ensureDirectoryExists(outputDir)
    oldDir = os.getcwd()
    os.chdir(outputDir)
    try:
        createHdfEmpty()
        createHdfDims()
    finally:
        os.chdir(oldDir)


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG", format=makeLogFormat(loggerName=True, fileLine=False))
    createTestData("test_data")
