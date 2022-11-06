#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Create some data files that can be used for testing.

    Is by no means extensive perhaps in the future it will. For now it is updated when issues are encountered.
"""
import logging
import os.path

import numpy as np

from argos.utils.dirs import ensureDirectoryExists
from argos.utils.logs import makeLogFormat

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




def createTestData(outputDir):
    """ Creates test data files in output directory
    """
    ensureDirectoryExists(outputDir)
    oldDir = os.getcwd()
    os.chdir(outputDir)
    try:
        createNetCdfTestData()

    finally:
        os.chdir(oldDir)


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG", format=makeLogFormat(loggerName=True, fileLine=False))
    createTestData("test_data")
