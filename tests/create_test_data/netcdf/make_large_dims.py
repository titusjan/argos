# -*- coding: utf-8 -*-
"""

/argos/mytests/large_dims.nc/my_var
"/argos/Mini Scanner Output/acceptance1.h5/samples/re"
"""

def main():

    from netCDF4 import Dataset
    rootgrp = Dataset("large_dims.nc", "w", format="NETCDF4")

    timeDim = rootgrp.createDimension("my_long_time_dim_name", 10000)
    lonDim = rootgrp.createDimension("lon", 2)
    latDim = rootgrp.createDimension("lat", 2)


    var = rootgrp.createVariable("my_var", "c",
                           ("my_long_time_dim_name", "lon", "lat"))

    print(var.shape)
    var[:] = 'p'

    rootgrp.close()




if __name__ == '__main__':

    main()
