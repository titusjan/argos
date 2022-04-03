# -s "/argos/2014-04-29_FEL-350/2014-04-29T11_32_032 shutters m1.h5/scan_procedure/procedure"

import numpy as np
import h5py


def main():

    with h5py.File("string.hdf5", "r") as root:
        ds = root['fixed_len_ascii_ds']
        print(type(ds[:]))
        print(type(ds[0]))

        ds = root['int dataset']
        print(type(ds[:]))
        print(type(ds[0]))


if __name__ == "__main__":
    main()

