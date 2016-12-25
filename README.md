Argos
==========

Argos is a GUI for viewing and exploring scientific data, written in Python and Qt. It has a
plug-in architecture that allows Argos to be extended to read new data formats. At the moment
plug-ins are included to read HDF-5, NetCDF-4, WAV, numpy binary files and various image formats,
but a plug-in can be written for any data that can be expressed as a Numpy array.

![argos_screen_shot](docs/screen_shots/argos_gui.png)

### Installing Argos

Argos works with Python 2.7 or Python 3.4 and higher. If you don't have Python yet, you might
consider to install the [Anaconda Python distribution](https://www.continuum.io/downloads), as it
comes with many of Argos' depencencies installed.

Argos requires at least [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro) and
[Numpy](http://www.numpy.org). It is strongly recommended to also install
[PyQtGraph](https://pyqtgraph.org) (version 0.10.0 or higher), which is required to visualize the
data as image or line plots. Without PyQtGraph the data can only be examined as tables or text.

Provided you use Python 3.5 or higher, you can install PyQt5 with `pip`. Otherwise you can download
it at the [Riverbank site](https://www.riverbankcomputing.com/software/pyqt/download5).

    %> pip install PyQt5
    %> pip install numpy
    %> pip install pyqtgraph
    %> pip install argos

The following dependencies are optional. You only need to install them if you want to read the
corresponding file formats. They can be installed with `pip install <package>` or downloaded from
their respective website.

| Python package                                       | File formats                    |
|------------------------------------------------------|---------------------------------|
| [h5py](http://www.h5py.org)                          | HDF-5                           |
| [netCDF4](http://unidata.github.io/netcdf4-python/)  | NetCDF (v3 and v4)              |
| [pillow](https://python-pillow.org/)                 | BMP, JPEG, PNG, TIFF, GIF, etc. |
| [scipy](https://www.scipy.org/)                      | Matlab & IDL save-files. WAV    |
| [pandas](https://www.pandas.org/)                    | Comma-separated files           |


### Starting Argos

After installation, Argos can be started from the command-line with

```
    %> argos [FILE [FILE ...]]
```

where `[FILE [FILE ...]]` are zero or more files or directories you want to view.

Argos remembers some persistent settings such as window position and size. If, for some reason,
you want Argos to reset to its initial state, you can use the `--reset` option.

```
    %> argos --reset
```

For a complete list of command line options, run argos with `-h'.

```
    %> argos -h
```

### Using Argos

The Argos main window consist of a central panel that holds a visualization surrounded by
smaller windows. The smaller windows can be moved around by dragging them holding their title bar.
They can be separated from the main window or can be docked at an at another position. Collectively
they are called the dock windows. You can use the `View` main menu to open and close them.

The main panel is called the (data) Inspector. In the `Inspector` main menu you can select a
different type: line plot, image plot, table, or text inspector. The current inspector type is
shown in the `Current inspector` dock window (in the upper left corner in the screen shot below).
If you want to have more than one inspector open at the same time, you can make a new main window
in the `File` main menu.

#### Selecting Data

The `Data Repository` dock window gives the list of files or directories that are available for
inspection. You can add files by selecting the `Open Files` from the `File` menu and directories
with the `Browse Directory` option. Argos will use the file extension to determine which plug-in
is used to open the file. The icon color of the tree items indicates which plug-ins is used. With
the `Open as` menu option you can force a certain plug-in to be used. If the plug-in gives an
error for that file, it will get a red triangle as icon (hover over the item to get a
tool-tip with the error message).

Note that the data repository is shared between all open
windows. That is, opening a file will add them in the `Data Repository` of all windows.

The repository is in the form of a tree. Expanding the items in the tree will automatically open
the underlying files. Collapsing an item will not close the the tree item, which is indicated by
the icon remaining the same. To close the underlying file, right-click the correponding tree item
and select `Close Item` from the context menu. The context menu also contains some other operations
that work on that tree item, which hopefully are obvious from their description.


#### Slicing the Data


Selecting an item in the repository will automatically place it in the `Data Collector` table.
If the item contains data that can be converted to an array, combobox and spinbox widgets will
appear in the table that enable you to specify the slice of the array that the inspector will
visualize.

For example, in the screen shots the `ColumnAmountO3` HDF-5 dataset is selected
and placed in the collector. It contains a world wide distribution of ozone in the athmosphere. This
is a two-dimensional dataset: the first dimension corresponds to longitude, the second to latitude.
These dimensions have no name since  the dataset has not associated *dimension scales*. Therefore,
Argos just calls them `Dim0` and `Dim1`.

In the screen shot at the top of the page, the inspector is a `2D Image Plot`. This is a
two-dimensional inspector so
there will appear two comboboxes in the table. The first for specifying which data dimension will be
mapped onto the Y-axis, `Dim0` in the example, and the second combobox determines the data dimension
used mapped to the X-axis as shown here.

![collector_2d](docs/screen_shots/collector_2d.png)

Now imagine that your inspector is a `1D Line Plot` inspector. As the name
implies this has only one independent variable (i.e. the X-axis). The data is two-dimensional so
only a sub-slice of the dataset can be visualized. There will be a combobox for specifying which
data dimension will be layed along the X-axis, and a spinbox for selecting the index for the other
dimension. Below you see the case that the line plot will draw row 360, or in Numpy
notation: `ColumnAmountO3[360, :]`

![collector_1d](docs/screen_shots/collector_1d.png)

Note that the HDF-5 example data from the screenshots can be downloaded
[here](http://www.hdfeos.org/zoo/index_openGESDISC_Examples.php#OMI) (2.4 MB).

#### Inspecting Data


Below the repository window are three dock windows that are layed out on top of each other, and
that can be brought to front by clicking their respective tab. They are for displaying meta data of
the item that is currently selected in the data repository (not the one in the data collector).

The `Properties` window contains a list of properties, such as the shape and element-type of the
data. These properties, by the way, can be added as columns in the data repository. By default only
the `name` property is show; right-click on the tree header to add extra columns.

The list of properties is fixed. In contrast the `Attributes` dock window give a list of meta data
that can be different for each selected item. Examples are HDF-5 or NetCDF attributes, or image
information attributes. Finallye, the `Dimensions` lists the dimension names and sizes of arrays.

