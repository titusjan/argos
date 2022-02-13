


# I only implemented the Python 2 variant of
# See: http://docs.h5py.org/en/latest/strings.html
# http://docs.h5py.org/en/latest/high/dataset.html#creating-and-reading-empty-or-null-datasets-and-attributes

import h5py
import numpy


# Doesn't seem to work, perhaps this is new. Let's try later
def make_empty_attr():
    """ Makes HDF-5 file with special cases 
    """
    with h5py.File("empty.hdf5", "w") as hdf:
        #Gives: AttributeError: 'module' object has no attribute 'Empty'
        ds_ints = hdf.create_dataset("emtpy attributes", (15,), dtype=int)
        ds_ints[:] = 15
        ds_ints.attrs["description"] = "A normal dataset with an empty attribute"
        ds_ints.attrs["emptyattr"] = h5py.Empty("f")

  

def make_empty_ds():
    """ Makes HDF-5 file emtpy dataset
    """
    with h5py.File("empty.hdf5", "w") as hdf:
        #Gives: AttributeError: 'module' object has no attribute 'Empty'
        ds_empty = hdf.create_dataset("EmptyDataset", data=h5py.Empty("f"))
        ds_empty.attrs["description"] = "An emtpy dataset"
        ds_empty.attrs["comments"] = "See http://docs.h5py.org/en/latest/high/dataset.html#creating-and-reading-empty-or-null-datasets-and-attributes"
  

if __name__ == '__main__':
    #make_empty_attr()
    make_empty_ds()
    
