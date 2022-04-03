#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Create some data files that can be used for testing.

    Is by no means extensive perhaps in the future it will. For now it is updated when issues are encountered.
"""
import logging
import os.path

import numpy as np

from argos.utils.dirs import ensureDirectoryExists
from argos.utils.logs import make_log_format

logger = logging.getLogger("create_test_data")


def createHdfTestData():
    """ Create files with the python h5py module.
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



def createTestData(outputDir):
    """ Creates test data files in output directory
    """
    ensureDirectoryExists(outputDir)
    oldDir = os.getcwd()
    os.chdir(outputDir)
    try:
        createHdfTestData()
    finally:
        os.chdir(oldDir)


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG", format=make_log_format(loggerName=True, fileLine=False))
    createTestData("test_data")
