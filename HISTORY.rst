.. :changelog:

History
=======

Note that version 0.3 will be the last release that supports Python 2.

0.4.2 (2022-07-24)
------------------

* Compound/stuctured HDF5 datasets can be nested.
* Can display JSON files (with comments https://github.com/sidneycadot/json_with_comments)
* Removed many harmless warnings.
* Small fixes


0.4.1 (2022-03-02)
------------------

*   Fix: don't import numpy during running setup.py

0.4.0 (2022-02-27)
------------------

*   Quick Look panel for showing quickly the contents of scalars and small arrays.
*   The Repository tree shows Kind, Element Type and Summary columns by default.
*   If one file or directory is opened, or given on the command line, it is expanded.
*   Only add a '-' item to the collector combo boxes if the array has less dimensions than the inspector.
*   The table inspector has "#8.4g" as the default format for floats. The tooltip shows all digits.
*   Added __main__.py so argos can be started with: python -m argos.
*   Fixed import in Line Plot and Image Plot inspectors (issue #20).
*   Fixed errors when running Argos with Python 3.10.


0.3.1 (2021-02-07)
------------------

*   Fixed error in style sheet.


0.3.0 (2021-02-07)
------------------

*   New legend in 2D image inspector
*   Extensive database of color maps and color map picker (CmLib).
*   Directories are listed in alphabetical order.
*   Image inspector: cross hair and axis ticks are displayed in the middle of the pixels.
*   Image inspector: added 'auto down-sample' config option (on by default).
    This improves performance for large images and reduces aliasing.
*   Added rectangle zoom mode in 1D line plot and 2D image plot inspectors (issue #8)
*   Zooming can be also done by dragging while holding the right mouse button (issue #8)
*   If possible, only informative dimensions (i.e. length > 1) are selected in the collector
    combo boxes. (issue #9)
*   Sliders next to the spinboxes in the collector panel
*   Fix: slices are updated in plot title when spinbox values change.
*   Fix: when table headers autosize was enabled, restarting argos could be slow for large tables.
*   Users can add/remove/configure plugins via the GUI.
*   Grouped the Details dock widgets together with repo viewer as they always apply to the selected item.
*   Properties tab shows chunking information for HDF5 and NetCDF data.
*   Updated style and layout.
*   Added --qt-style and --qss command line options. Using Qt Fusion style as default.
*   Displays informative message in case the plot remains empty.
*   Accepts unix-like patterns on the Windows command line. E.g. 'argos \*.h5' opens all files with the h5 extension.
*   Persistent settings are stored in json file instead of QSettings.
*   Added -c command line option for specifying the general configuration file. Settings profiles are thus obsolete
    and have been removed.
*   Added --log-config command line option for specifying the logging configuration file.
*   Collapsing an item in the data tree closes the underlying file or resources.
*   Open Exdir files read-only
*   Ctrl-C copies all selected cells in the Table instpector to the clipboard.

0.2.2 (2020-03-28)
---------------------

* Exdir file format plugin. (Thanks to Lui Habl).


0.2.1 (2017-01-12)
------------------
*   Fix: in PyQt 5.7 the slot decorator wouldn't connect anymore if the class didn't derive
    from QObject.


0.2.0 (2017-01-01)
------------------
*   First usable release.


0.1.0 (2014-11-01)
------------------
*   First release on PyPI.
