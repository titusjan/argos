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

def createNetCdfTestData():
    """ Create files with the python netCDF4 module

        From netCDF4 tutorial:
            https://unidata.github.io/netcdf4-python/netCDF4/index.html
            https://github.com/Unidata/netcdf4-python/blob/master/examples/tutorial.py
    """
    from netCDF4 import Dataset, Group, Variable

    with Dataset("normal.nc", "w", format="NETCDF4") as rootgrp:
        rootgrp.description = "File with normal use cases"

        level = rootgrp.createDimension("level", None)
        time = rootgrp.createDimension("time", None)
        lat = rootgrp.createDimension("lat", 73)
        lon = rootgrp.createDimension("lon", 144)

        times = rootgrp.createVariable('time','f8',('time',))
        levels = rootgrp.createVariable('level','i4',('level',))
        latitudes = rootgrp.createVariable('lat','f4',('lat',))
        longitudes = rootgrp.createVariable('lon','f4',('lon',))

        latitudes[:] = np.arange(-90,91,2.5)
        longitudes[:] = np.arange(-180,180,2.5)


    with Dataset("dim_size_0.nc", "w", format="NETCDF4") as rootgrp:
        rootgrp.description = "Contains datasets with dimensions of size 0"

        rootgrp.createDimension("fixed", 0)
        rootgrp.createDimension("unlimited", None)

        rootgrp.createVariable('1d_fixed','i4',('fixed',))
        rootgrp.createVariable('1d_unlim','i4',('unlimited',))
        rootgrp.createVariable('2d','f4', ('fixed','unlimited'))


    with Dataset("scalars.nc", "w", format="NETCDF4") as rootgrp:
        rootgrp.description = "Contains datasets with scalars"
        scalar = rootgrp.createVariable('my_scalar','i4',)
        scalar[:] = 66

        maskedScalar = rootgrp.createVariable('masked_scalar','i4', fill_value=-99)
        maskedScalar.description = "A scalar set to the fill value"
        maskedScalar[:] = -99



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
        try:
            createNetCdfTestData()
        except Exception as ex:
            logger.error("Error while creating NetCDF data. Aborted")
            logger.exception(ex)

        try:
            createHdfTestData()
        except Exception as ex:
            logger.error("Error while creating HDF5 data. Aborted")
            logger.exception(ex)

    finally:
        os.chdir(oldDir)


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG", format=make_log_format(loggerName=True, fileLine=False))
    createTestData("test_data")
