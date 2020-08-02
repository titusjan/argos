.. :changelog:

History
=======


0.3.0 (????-??-??)
------------------

*   New legend in 2D image inspector
*   Extensive database of color maps and color map picker (CmLib).
*   Directories are listed in alphabetical order.
*   Added rectangle zoom mode in 1D line plot and 2D image plot inspectors (issue #8)
*   Zooming can be also done by dragging while holding the right mouse button (issue #8)
*   If possible, only informative dimensions (i.e. length > 1) are selected in the collector
    comboboxes. (issue #9)
*   Users can add/remove/configure plugins via the GUI.
*   Grouped Details dock widgets together with repo viewer as they always apply to the selected item.
*   Updated style and layout.
*   Added --qt-style and --qss command line options. Using Qt Fusion style as default.
*   Persistent settings are stored in json file instead of QSettings
*   User can select config file that is used. Settings profiles are thus obsolete and removed.
*   Open Exdir files read-only

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
