Argos
==========

Argos is a GUI for viewing and exploring scientific data, written in Python and Qt. It has a
plug-in architecture that allows it to be extended to read new data formats. At the moment
plug-ins are included to read HDF-5, NetCDF-4, WAV, numpy binary files and various image formats,
but a plug-in could be written for any data that can be expressed as a Numpy array.

### Installing Argos

Argos works with Python 2.7 or Python 3.4 and higher. If you don't have Python yet, consider to
use the [Anaconda Python distribution](https://www.continuum.io/downloads), as it comes with many
of Argos' depencencies installed.

Argos requires at least [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro) and
[Numpy](http://www.numpy.org). It is strongly recommended to also install
[PyQtGraph](https://pyqtgraph.org) (version 0.10.0 or higher), which is required to visualize the
data as image plots or line plots. Without PyQtGraph the data can only be examined as tables or
text.

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
| [pandas](http://pandas.pydata.org/)                  | Comma-separated files           |


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

#### Trouble shooting

If you start `argos` and nothing happens, you probably didn't install `PyQt` or `numpy`. You can
try to start argos as follows to get more information

```
    %> python -m argos.main
```


### Using Argos

The Argos main window consists of a central panel that holds a visualization, and of smaller
windows that surround the main pannel. The smaller windows can be moved around by dragging them at
their title bar. They can be separated from the main window or can be docked at an at another
position. Collectively they are called the dock windows. You can open and close them via the `View`
main menu.

![argos_screen_shot](docs/screen_shots/argos_gui.png)

The main panel is called the (data) Inspector. From the `Inspector` main menu you can select a
different type: line plot, image plot, table, or text inspector. The current inspector type is
shown in the `Current inspector` dock window (in the upper left corner in the screen shot). If you
want to have more than one inspector open at the same time, you can select `New Window` from the
`File` menu.


#### Selecting Data

The HDF-5 file that is used in the screenshot and in the examples below can be
downloaded  [here](http://www.hdfeos.org/zoo/index_openGESDISC_Examples.php#OMI) (2.4 MB).

The `Data Repository` dock window gives the list of files and directories that are available for
inspection. The repository has the form of a tree, or more precisely a list of trees (a forest).
You can add files by selecting the `Open Files` from the `File` menu, and add directories with the
`Browse Directory` option. Argos uses the file extension to determine which plug-in to use for
opening the file. The icon color of the tree items indicates which plug-in was used. With the
`Open as` menu option you can force Argos to open a file with the a certain plug-in. If a plug-in
raises an error while opening a file, it will get a red triangle as icon (hover over the item to
get a tool-tip with the error message).

Expanding the items in the tree will automatically open the underlying files. However, collapsing
an item will not close the the tree item, as is indicated by the icon remaining the same. To close
the underlying file, right-click the corresponding tree item and select `Close Item` from the
context menu. This context menu also contains some other operations that work on that tree item,
which hopefully are clear from their description.

Note that the data repository is shared between all Argos main windows. That is, opening a file
will add a new item to the `Data Repository` tree of all open windows.


#### Slicing Data

Selecting an item in the repository will automatically place it in the `Data Collector` table.
If the item contains data that can be converted to an array, combobox and spinbox widgets will
appear in the table. These enable you to specify a slice of the array that the inspector will then
visualize.

In the screen shot for instance, the `ColumnAmountO3` HDF-5 dataset is selected
and placed in the collector. This is a two-dimensional dataset, it contains a world wide
distribution of ozone in the atmosphere. The first dimension corresponds to latitude, the second to
longitude. These dimensions have no name since the dataset has no associated
[dimension scales](http://docs.h5py.org/en/latest/high/dims.html). Therefore, Argos just calls
them `Dim0` and `Dim1`.

The inspector in the screen shot is a `2D Image Plot`. This is a two-dimensional inspector so there
will appear two comboboxes in the table: the first specifies which dimension will be mapped onto
the Y-axis (`Dim0` in the example) and the second determines the data dimension that is mapped to
the X-axis.

![collector_2d](docs/screen_shots/collector_2d.png)

Now imagine that your inspector is a `1D Line Plot` inspector. As the name
implies this has only one independent variable (the X-axis). The data is two-dimensional so only a
sub-slice of the dataset can be visualized. The collector will now contain a combobox for
specifying which data dimension will be layed along the X-axis, and a spinbox for selecting the
index of the other dimension. Below you see the case that the line plot will draw row 360, or in
Numpy notation: `ColumnAmountO3[360, :]`. By default Argos will put the first array dimension(s) in
the spinbox(es), and select the fasted changing array dimension(s) in the combobox(es).

![collector_1d](docs/screen_shots/collector_1d.png)


#### Inspecting Data

The `Application Settings` dock window, located to the right of the inspector, contains settings
for configuring the current inspector. If you click on a config value, an appropriate widget
will appear for editing, together with a reset button <img src="argos/img/snipicons/reset-l.svg" width="16" height="16">
that will reset the config value to its default when clicked. The settings are hierarchical so that
related settings can be grouped together in a brance. Branches also have a reset button, so for 
instance by clicking on the reset button of the `y-axis` config value branch, all settings
pertaining to the Y-axis are reset. The reset button in the dark gray bar at the top, the one that
says `2D image plot` in the screen shot, will reset all config values of that inspector.

A few of the config settings are explained below. It is not a complete list, many of the settings
will be clear from their name. I also urge you to experiment yourself by just trying new values.
You can always go back by resetting the configuration of the complete inspector with the reset
button in the dark grey row at the top. Note that some branches are collapsed by default to hide
the infrequently used configuration options. For instance the `auto-range` item can be expanded for
further tweaking of the auto-range method.

##### 1D Line Plot Inspector

The `1D Line Plot` inspector contains a line plot widget. It uses [PyQtGraph](http://pyqtgraph.org/)
as the underlying plot engine. Just as in PyQtGraph you can use the left mouse button to pan,
and the mouse wheel to zoom in and out. If you drag while your mouse cursor in above the X or Y
axis, panning will be only in that direction. Similarly zooming with the mouse wheel will will only
zoom on that axis. The right mouse button will bring up a context menu with choices to reset one,
or both, axes to their default range (i.e. setting the axis auto-range on).

If the axis auto-range mode is on, the axis range is calculated from the plot data. By default this
is delegated to PyQtGraph, but by setting the `y-axis/range/autorange/method` option, you can let
the auto-range method discard a percentage of the outliers.

If the axis auto-range mode is off, you can set the axis range manually in the `range/min` and
`range/max` options. The range will remain fixed if you select a new slice with the spinbox.
Autorange will be turned off as soon as you zoom or pan the data. You can turn it on again in the
`...-axis/range/autorange` option, the inspector context menu, or by clicking the small button
labeled 'A' in the lower left corner of the figure.

The plot title can be modified with the `title` config option via an editable combobox widget. You
can enter any title you want but be aware that the title may be incorrect as soon as you pick a
new variable from the repository. Therefore a few properties can be written in between braces.
These will then be updated dynamically whenever a new repo item is picked. For example, `{name}`
will be substituted with the name of the selected item.

*   `{name}`     : name of the selected item from the repository.
*   `{path}`     : full path of the items leading up to the selected item. Might be long!
*   `{base-name}`: name of the file that contains the item.
*   `{dir-name}` : directory of the file that contains the item. Might be long!
*   `{file-name}`: full file name (dir-name + '/' + base-name). Might be long!
*   `{slices}`   : information about the selected array slice in Numpy notation. E.g. `[360, :]`
*   `{unit}`     : the unit of the item in parenthesis, or the empty string if no unit is available.
*   `{raw-unit}` : the unit of the item as-is, that is, without parenthesis.

Furthermore, PyQtGraph uses HTML for the plot title so you can make fancy titles such as
`<small>{name} <span style="color:#FF0066">{slices}</span></small>`. This also means that you must
escape the `<`, `>` and `&` characters by using `&lt;`, `&gt;`, `&amp;` instead!

The `x-axis/label` and `y-axis/label` settings can be edited in the same way as the `title`.

The editable comboboxes will remember entered values. If you want to remove an item from a
combobox, highlight it in and then press delete. You can also press CTRL-delete while you are
editing to remove the current item.

The `pen` branch holds config items that determine how the plot curve is drawn. Make sure you have
at least one of the `line` and `symbol` checkmarks checked, or the curve will be invisible.
Anti-aliasing is turned on by default. This can be slow, especially in combination with a
line width other than 1.0, so if you have large plots you might want to turn it off.

##### 2D Image Plot Inspector

The axes configuration items of the 2D image plot work in the same manner as for the 1D line plot.
Next to that, the image plot has a `color range` that determines the minumum and maxiumum
values of the color scale. The color range too can be in auto-range mode, or can be set
manually. On the left side of the plot, you can see the color range visualized as the blue
rectangle between the color bar and the values. You can drag the rectangle to shift the
range and make the image lighter or darker. You can also drag ene of the edges of the rectangle and
thus change the contrast of the rendered image.

Inside the blue rectange you see a side-ways histogram, which gives an indication of how many
pixels have a certain value. This may assist you in choosing the best color range. By dragging the
numbers of the color scale you can pan the histogram. Using your mouse wheel while the cursor is
above the histogram will zoom in or out. The precise values of the histogram range can be seen in
the `histogram range` item in the config tree. Just like the other range-settings this has an
auto-range mode that can be turned on or off.

By checking the `cross hair` config option you can bring up two line plots to the side of the
figure (see the screen shot above). A horizontal and vertical line are drawn at the cursor position
and the plots will contain a cross-section of the values along those lines.

##### Table Inspector

This inspector is useful for examining the exact values of your data. You can change the size of
the table cells via the `row height` and `column width` settings. By checking the
`auto row heights` and/or the `auto column widths` check boxes, you can configure the table
inspector to calculate the cell sizes dynamically from their contents. Note that this can be slow
for large tables.  So, as an optimization, if the table has more than 1000 elements only the
currently selected cell is used to calculate the height and width, and this is applied to all other
cells. If a table has more than 10000 rows or columns, auto resizing is disabled.

If your selected repository item is a structured array, i.e. an array having fields, all fields are
displayed in a separate column by default. If you uncheck the `separate fields` checkbox, all
fields of are combined in a single cell as follows: `(field1, field2, ...)`.

You can change how the data in the cells is formatted with the config options under the
`format specifier` branch. Which setting is used depends on your data type: the `integers` format
setting is used if the data in the cell is an integer, `other numbers` is used for floating point,
rational, or complex numbers; and any data that is not a string or a number is formatted with the
`other types` format code. For instance, setting the `other numbers` to `.2e` will display all
floating point data in scientific notation with two digits behind the decimal point.

The format codes must be a `format_spec` from the new-style Python formatting. You can think of 
them as new-style formatting codes, but without the braces and the colon. If you want to use a 
complete format string, i.e. _with_ the braces and the colon, you must put your format string 
between quotes. For example, using `'hello {:.2e}'` will prepend "hello" to the data values. Take 
a look at the [Format Specification Mini-Language](https://docs.python.org/3/library/string.html#format-specification-mini-language)
from the Python documentation to see what's possible. 

##### Text Inspector

The `Text` inspector contains a _read-only_ text editor widget that shows the contents of a single
array element. If your data consists of a large strings, especially strings of multiple lines,
examining it in a text editor works better than using a table and resizing the cell sizes. Also
the `word wrap` settings has more options here. To see this for yourself, download the example file
from the screenshot [here](http://www.hdfeos.org/zoo/index_openGESDISC_Examples.php#OMI) (2.4 MB),
and look at the `HDFEOS INFORMATION/StructMetadata.0` dataset in both the table inspector and the
text inspector.


#### Viewing Metadata

Below the repository window (in the lower left corner of the screen shot) are three dock windows 
that are layed out on top of each other, and which can be brought to front by clicking their 
respective tab. They are for displaying meta data of the item that is currently selected in the 
data repository (note: not the item in the data collector).

The `Dimensions` dock window lists the dimension names and sizes of arrays. The `Attributes` window lists
the HDF or NetCDF attributes of a group or dataset/variable. Other file formats may contain similar
meta data, which is then also displayed here.

The `Properties` window contains a list of properties, such as the shape and element-type of the
selected item. In contrast to the `Attributes` this list is fixed, all repo items always have the
same list of properties (although their contents may be empty). These properties, by the way, can
be added as columns in the data repository. By default only the `name` property is shown;
right-click on the repository tree header to add extra columns.
