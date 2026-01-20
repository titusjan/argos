# -*- coding: utf-8 -*-

# This file is part of Argos.
#
# Argos is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Argos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Argos. If not, see <http://www.gnu.org/licenses/>.

"""
    Dialog for exporting data to various file formats.
"""

import logging
import os

import numpy as np

from argos.qt import QtCore, QtWidgets

logger = logging.getLogger(__name__)


# Supported export formats with their file extensions and descriptions
EXPORT_DATA_FORMATS = [
    ("CSV", "*.csv", "Comma-Separated Values"),
    ("NumPy", "*.npy", "NumPy Binary Format"),
    ("HDF5", "*.h5 *.hdf5", "Hierarchical Data Format 5"),
    ("Zarr", "*.zarr", "Zarr Array Format"),
]


class ExportDataDialog(QtWidgets.QDialog):
    """ Dialog that allows exporting data to various file formats.
    """

    def __init__(self, mainWindow, parent=None):
        """ Constructor

            Args:
                mainWindow: the Argos main window.
        """
        super(ExportDataDialog, self).__init__(parent=parent)
        self.setWindowTitle("Export Data")
        self.setModal(True)

        self._mainWindow = mainWindow

        self._setupWidgets()

    def _setupWidgets(self):
        """ Setup the dialog widgets.
        """
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        # Data info group
        self.infoGroupBox = QtWidgets.QGroupBox("Data Info")
        self.infoLayout = QtWidgets.QFormLayout()
        self.infoGroupBox.setLayout(self.infoLayout)

        self.shapeLabel = QtWidgets.QLabel("--")
        self.dtypeLabel = QtWidgets.QLabel("--")
        self.sizeLabel = QtWidgets.QLabel("--")

        self.infoLayout.addRow("Shape:", self.shapeLabel)
        self.infoLayout.addRow("Data Type:", self.dtypeLabel)
        self.infoLayout.addRow("Size:", self.sizeLabel)

        self.mainLayout.addWidget(self.infoGroupBox)

        # Format selection group
        self.formatGroupBox = QtWidgets.QGroupBox("Export Format")
        self.formatLayout = QtWidgets.QVBoxLayout()
        self.formatGroupBox.setLayout(self.formatLayout)

        self.formatButtonGroup = QtWidgets.QButtonGroup(self)
        self.formatRadioButtons = {}

        for i, (fmt, ext, desc) in enumerate(EXPORT_DATA_FORMATS):
            radioButton = QtWidgets.QRadioButton(f"{fmt} - {desc}")
            radioButton.setToolTip(f"Export as {desc} ({ext})")
            self.formatButtonGroup.addButton(radioButton, i)
            self.formatLayout.addWidget(radioButton)
            self.formatRadioButtons[fmt] = radioButton

        # Default to CSV
        self.formatRadioButtons["CSV"].setChecked(True)

        self.mainLayout.addWidget(self.formatGroupBox)

        # Buttons layout
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addLayout(self.buttonLayout)

        self.buttonLayout.addStretch()

        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)
        self.buttonLayout.addWidget(self.cancelButton)

        self.exportButton = QtWidgets.QPushButton("Export...")
        self.exportButton.setDefault(True)
        self.exportButton.clicked.connect(self._onExport)
        self.buttonLayout.addWidget(self.exportButton)

        self.resize(QtCore.QSize(400, 300))

    def finalize(self):
        """ Is called before destruction (when closing).
            Can be used to clean-up resources.
        """
        pass

    def showEvent(self, event):
        """ Called when the dialog is shown. Updates the data info.
        """
        super(ExportDataDialog, self).showEvent(event)
        self._updateDataInfo()

    def _updateDataInfo(self):
        """ Update the data info labels.
        """
        data = self._getData()

        if data is None:
            self.shapeLabel.setText("No data available")
            self.dtypeLabel.setText("--")
            self.sizeLabel.setText("--")
            self.exportButton.setEnabled(False)
            return

        self.exportButton.setEnabled(True)
        self.shapeLabel.setText(str(data.shape))
        self.dtypeLabel.setText(str(data.dtype))

        # Calculate size in human-readable format
        size_bytes = data.nbytes
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

        self.sizeLabel.setText(size_str)

    def _getData(self):
        """ Get the current data from the collector.
        """
        try:
            collector = self._mainWindow.collector
            if not collector.rtiIsSliceable:
                return None

            arrayWithMask = collector.getSlicedArray()
            if arrayWithMask is None:
                return None

            # Get the data array (without mask for simplicity)
            return arrayWithMask.data
        except Exception as ex:
            logger.warning(f"Failed to get data: {ex}")
            return None

    def _getSelectedFormat(self):
        """ Returns the selected format tuple (name, extension, description).
        """
        selectedId = self.formatButtonGroup.checkedId()
        return EXPORT_DATA_FORMATS[selectedId]

    def _getDefaultExtension(self):
        """ Returns the default file extension for the selected format.
        """
        fmt, ext, _ = self._getSelectedFormat()
        # Extract first extension (e.g., "*.csv" -> ".csv")
        return ext.split()[0].replace("*", "")

    def _onExport(self):
        """ Handle the export button click.
        """
        selectedFmt, selectedExt, selectedDesc = self._getSelectedFormat()

        # Build filter string with selected format first
        selectedFilter = f"{selectedDesc} ({selectedExt})"
        otherFilters = []
        for f, e, d in EXPORT_DATA_FORMATS:
            filterStr = f"{d} ({e})"
            if f != selectedFmt:
                otherFilters.append(filterStr)

        filterString = selectedFilter + ";;" + ";;".join(otherFilters) + ";;All Files (*)"

        filePath, returnedFilter = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Data",
            "",
            filterString
        )

        if not filePath:
            return

        # Determine format from file extension first
        ext = os.path.splitext(filePath)[1].lower()

        # If no extension, determine from selected filter in dialog
        if not ext:
            if "CSV" in returnedFilter or "*.csv" in returnedFilter:
                filePath += ".csv"
                ext = ".csv"
            elif "NumPy" in returnedFilter or "*.npy" in returnedFilter:
                filePath += ".npy"
                ext = ".npy"
            elif "HDF5" in returnedFilter or "*.h5" in returnedFilter:
                filePath += ".h5"
                ext = ".h5"
            elif "Zarr" in returnedFilter or "*.zarr" in returnedFilter:
                filePath += ".zarr"
                ext = ".zarr"
            else:
                # Fall back to radio button selection
                filePath += self._getDefaultExtension()
                ext = os.path.splitext(filePath)[1].lower()

        logger.info(f"Exporting data to: {filePath} with extension: {ext}")

        data = self._getData()
        if data is None:
            self._showExportError("No data available for export")
            return

        success = False
        if ext == '.csv':
            success = self._exportAsCsv(data, filePath)
        elif ext == '.npy':
            success = self._exportAsNumpy(data, filePath)
        elif ext in ('.h5', '.hdf5'):
            success = self._exportAsHdf5(data, filePath)
        elif ext == '.zarr':
            success = self._exportAsZarr(data, filePath)
        else:
            # Default to CSV for unknown extensions
            logger.warning(f"Unknown extension '{ext}', defaulting to CSV")
            success = self._exportAsCsv(data, filePath)

        if success:
            self.accept()

    def _exportAsCsv(self, data, filePath):
        """ Export data as CSV using pandas.
        """
        logger.info(f"Exporting to CSV: {filePath}")
        try:
            import pandas as pd

            # Handle different dimensionalities
            if data.ndim == 1:
                df = pd.DataFrame(data, columns=['value'])
            elif data.ndim == 2:
                df = pd.DataFrame(data)
            else:
                # For higher dimensions, flatten or reshape
                # Reshape to 2D: combine all but last dimension
                shape = data.shape
                new_shape = (-1, shape[-1]) if len(shape) > 1 else (-1,)
                reshaped = data.reshape(new_shape)
                df = pd.DataFrame(reshaped)

            df.to_csv(filePath, index=True)
            logger.info(f"Successfully exported CSV to: {filePath}")
            return True
        except ImportError:
            self._showExportError("pandas is required for CSV export. Install with: pip install pandas")
            return False
        except Exception as ex:
            self._showExportError(f"Failed to export CSV: {ex}")
            return False

    def _exportAsNumpy(self, data, filePath):
        """ Export data as NumPy binary format.
        """
        logger.info(f"Exporting to NumPy: {filePath}")
        try:
            np.save(filePath, data)
            logger.info(f"Successfully exported NumPy to: {filePath}")
            return True
        except Exception as ex:
            self._showExportError(f"Failed to export NumPy: {ex}")
            return False

    def _exportAsHdf5(self, data, filePath):
        """ Export data as HDF5 using h5py or xarray.
        """
        logger.info(f"Exporting to HDF5: {filePath}")
        try:
            import xarray as xr

            # Create dimension names based on data shape
            dims = [f"dim_{i}" for i in range(data.ndim)]

            # Create xarray DataArray and save
            da = xr.DataArray(data, dims=dims, name="data")
            ds = da.to_dataset()
            ds.to_netcdf(filePath, engine='h5netcdf')
            logger.info(f"Successfully exported HDF5 to: {filePath}")
            return True
        except ImportError:
            # Fall back to h5py
            try:
                import h5py
                with h5py.File(filePath, 'w') as f:
                    f.create_dataset('data', data=data)
                logger.info(f"Successfully exported HDF5 to: {filePath}")
                return True
            except ImportError:
                self._showExportError("xarray or h5py is required for HDF5 export. Install with: pip install xarray h5netcdf")
                return False
        except Exception as ex:
            self._showExportError(f"Failed to export HDF5: {ex}")
            return False

    def _exportAsZarr(self, data, filePath):
        """ Export data as Zarr format using xarray.
        """
        logger.info(f"Exporting to Zarr: {filePath}")
        try:
            import xarray as xr

            # Create dimension names based on data shape
            dims = [f"dim_{i}" for i in range(data.ndim)]

            # Create xarray DataArray and save
            da = xr.DataArray(data, dims=dims, name="data")
            ds = da.to_dataset()
            ds.to_zarr(filePath, mode='w')
            logger.info(f"Successfully exported Zarr to: {filePath}")
            return True
        except ImportError:
            self._showExportError("xarray and zarr are required for Zarr export. Install with: pip install xarray zarr")
            return False
        except Exception as ex:
            self._showExportError(f"Failed to export Zarr: {ex}")
            return False

    def _showExportError(self, message):
        """ Show an error message dialog.
        """
        logger.error(message)
        QtWidgets.QMessageBox.critical(
            self,
            "Export Error",
            message,
            QtWidgets.QMessageBox.Ok
        )
