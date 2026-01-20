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
    Dialog for exporting visualizations to image files.
"""

import logging
import os

from argos.qt import QtCore, QtGui, QtWidgets, QtSvg

logger = logging.getLogger(__name__)


# Supported export formats with their file extensions and descriptions
EXPORT_FORMATS = [
    ("PNG", "*.png", "Portable Network Graphics"),
    ("SVG", "*.svg", "Scalable Vector Graphics"),
    ("TIFF", "*.tiff *.tif", "Tagged Image File Format"),
]


class ExportImageDialog(QtWidgets.QDialog):
    """ Dialog that allows exporting plot items to image files.
    """

    def __init__(self, mainWindow, parent=None):
        """ Constructor

            Args:
                mainWindow: the Argos main window.
        """
        super(ExportImageDialog, self).__init__(parent=parent)
        self.setWindowTitle("Export Plot")
        self.setModal(True)

        self._mainWindow = mainWindow

        self._setupWidgets()

    def _setupWidgets(self):
        """ Setup the dialog widgets.
        """
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        # Thumbnail preview
        self.previewGroupBox = QtWidgets.QGroupBox("Preview")
        self.previewLayout = QtWidgets.QVBoxLayout()
        self.previewGroupBox.setLayout(self.previewLayout)

        self.thumbnailLabel = QtWidgets.QLabel()
        self.thumbnailLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.thumbnailLabel.setMinimumSize(300, 200)
        self.thumbnailLabel.setStyleSheet("QLabel { background-color: #f0f0f0; border: 1px solid #ccc; }")
        self.previewLayout.addWidget(self.thumbnailLabel)

        self.mainLayout.addWidget(self.previewGroupBox)

        # Export options group
        self.optionsGroupBox = QtWidgets.QGroupBox("Include in Export")
        self.optionsLayout = QtWidgets.QVBoxLayout()
        self.optionsGroupBox.setLayout(self.optionsLayout)

        self.includeColorScaleCheckbox = QtWidgets.QCheckBox("Color Scale")
        self.includeColorScaleCheckbox.setChecked(True)
        self.includeColorScaleCheckbox.setToolTip("Include the color scale/legend in the exported image")
        self.includeColorScaleCheckbox.stateChanged.connect(self._updateThumbnail)
        self.optionsLayout.addWidget(self.includeColorScaleCheckbox)

        self.includeHistogramCheckbox = QtWidgets.QCheckBox("Histogram")
        self.includeHistogramCheckbox.setChecked(True)
        self.includeHistogramCheckbox.setToolTip("Include the histogram in the exported image")
        self.includeHistogramCheckbox.stateChanged.connect(self._updateThumbnail)
        self.optionsLayout.addWidget(self.includeHistogramCheckbox)

        self.mainLayout.addWidget(self.optionsGroupBox)

        # Format selection group
        self.formatGroupBox = QtWidgets.QGroupBox("Export Format")
        self.formatLayout = QtWidgets.QVBoxLayout()
        self.formatGroupBox.setLayout(self.formatLayout)

        self.formatButtonGroup = QtWidgets.QButtonGroup(self)
        self.formatRadioButtons = {}

        for i, (fmt, ext, desc) in enumerate(EXPORT_FORMATS):
            radioButton = QtWidgets.QRadioButton(f"{fmt} - {desc}")
            radioButton.setToolTip(f"Export as {desc} ({ext})")
            self.formatButtonGroup.addButton(radioButton, i)
            self.formatLayout.addWidget(radioButton)
            self.formatRadioButtons[fmt] = radioButton

        # Default to PNG
        self.formatRadioButtons["PNG"].setChecked(True)

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

        self.resize(QtCore.QSize(400, 500))

    def finalize(self):
        """ Is called before destruction (when closing).
            Can be used to clean-up resources.
        """
        pass

    def showEvent(self, event):
        """ Called when the dialog is shown. Captures and displays the thumbnail.
        """
        super(ExportImageDialog, self).showEvent(event)
        self._updateThumbnail()

    def _updateThumbnail(self):
        """ Capture the current plot and display it as a thumbnail.
        """
        pixmap = self._captureCurrentView()

        if pixmap is None:
            self.thumbnailLabel.setText("No plot available")
            return

        try:
            # Scale to fit the label while maintaining aspect ratio
            scaledPixmap = pixmap.scaled(
                self.thumbnailLabel.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )
            self.thumbnailLabel.setPixmap(scaledPixmap)
        except Exception as ex:
            logger.warning(f"Failed to update thumbnail: {ex}")
            self.thumbnailLabel.setText("Preview not available")

    def _getExportOptions(self):
        """ Get the current export options from checkboxes.
        """
        return {
            'colorScale': self.includeColorScaleCheckbox.isChecked(),
            'histogram': self.includeHistogramCheckbox.isChecked(),
        }

    def _captureCurrentView(self):
        """ Capture the current view based on selected options.
        """
        inspector = self._mainWindow.inspector
        options = self._getExportOptions()

        # Check if this is an image plot inspector with the relevant components
        if hasattr(inspector, 'graphicsLayoutWidget'):
            return self._captureImagePlotWithOptions(inspector, options)
        else:
            # Fall back to basic plot capture
            plotItem = self._getPlotWidget()
            if plotItem is not None:
                return self._captureAsPixmap(plotItem)
        return None

    def _captureImagePlotWithOptions(self, inspector, options):
        """ Capture an image plot with the specified options.
        """
        try:
            # Get the graphics layout widget
            graphicsWidget = inspector.graphicsLayoutWidget

            # If all options are off, just capture the main plot
            if not any(options.values()):
                return self._capturePyQtGraphAsPixmap(inspector.imagePlotItem)

            # Temporarily hide/show elements based on options
            originalStates = {}

            # Handle color legend (contains both color scale and histogram)
            if hasattr(inspector, 'colorLegendItem'):
                colorLegend = inspector.colorLegendItem
                originalStates['colorLegendVisible'] = colorLegend.isVisible()

                # Get original histogram state from the inspector's config
                if hasattr(inspector, 'config') and hasattr(inspector.config, 'showHistCti'):
                    originalStates['histogramVisible'] = inspector.config.showHistCti.configValue
                else:
                    originalStates['histogramVisible'] = True  # Default assumption

                # Show color legend if either colorScale or histogram is checked
                shouldShowColorLegend = options['colorScale'] or options['histogram']
                colorLegend.setVisible(shouldShowColorLegend)

                # Control histogram visibility independently
                if shouldShowColorLegend and hasattr(colorLegend, 'showHistogram'):
                    colorLegend.showHistogram(options['histogram'])

            # Capture the widget
            pixmap = graphicsWidget.grab()

            # Restore original states
            if hasattr(inspector, 'colorLegendItem'):
                colorLegend = inspector.colorLegendItem
                # Restore histogram first (before restoring color legend visibility)
                if hasattr(colorLegend, 'showHistogram'):
                    colorLegend.showHistogram(originalStates['histogramVisible'])
                # Then restore color legend visibility
                colorLegend.setVisible(originalStates['colorLegendVisible'])

            return pixmap

        except Exception as ex:
            logger.warning(f"Failed to capture image plot with options: {ex}")
            # Fall back to capturing just the plot item
            if hasattr(inspector, 'imagePlotItem'):
                return self._capturePyQtGraphAsPixmap(inspector.imagePlotItem)
            return None

    def _captureAsPixmap(self, widget):
        """ Capture a QWidget as a QPixmap.
        """
        if isinstance(widget, QtWidgets.QWidget):
            return widget.grab()
        return None

    def _capturePyQtGraphAsPixmap(self, plotItem):
        """ Capture a PyQtGraph plot item as a QPixmap.
        """
        try:
            import pyqtgraph as pg
            import pyqtgraph.exporters
            exporter = pg.exporters.ImageExporter(plotItem)
            qimage = exporter.export(toBytes=True)
            pixmap = QtGui.QPixmap.fromImage(qimage)
            return pixmap
        except Exception as ex:
            logger.warning(f"Failed to capture PyQtGraph plot: {ex}")
            return None

    def _getPlotWidget(self):
        """ Returns the plot widget from the current inspector.
        """
        try:
            return self._mainWindow.inspector.getPlotItem()
        except NotImplementedError:
            logger.warning("Current inspector does not support image export")
            return None
        except Exception as ex:
            logger.error(f"Error getting plot item: {ex}")
            return None

    def _getSelectedFormat(self):
        """ Returns the selected format tuple (name, extension, description).
        """
        selectedId = self.formatButtonGroup.checkedId()
        return EXPORT_FORMATS[selectedId]

    def _getFileFilter(self):
        """ Returns the file filter string for the file dialog.
        """
        fmt, ext, desc = self._getSelectedFormat()
        return f"{desc} ({ext})"

    def _getDefaultExtension(self):
        """ Returns the default file extension for the selected format.
        """
        fmt, ext, _ = self._getSelectedFormat()
        # Extract first extension (e.g., "*.png" -> ".png")
        return ext.split()[0].replace("*", "")

    def _onExport(self):
        """ Handle the export button click.
        """
        selectedFmt, selectedExt, selectedDesc = self._getSelectedFormat()

        # Build filter string with selected format first
        selectedFilter = f"{selectedDesc} ({selectedExt})"
        otherFilters = []
        for f, e, d in EXPORT_FORMATS:
            filterStr = f"{d} ({e})"
            if f != selectedFmt:
                otherFilters.append(filterStr)

        filterString = selectedFilter + ";;" + ";;".join(otherFilters) + ";;All Files (*)"

        filePath, returnedFilter = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Plot",
            "",
            filterString
        )

        if not filePath:
            return

        # Determine format from file extension first
        ext = os.path.splitext(filePath)[1].lower()

        # If no extension, determine from selected filter in dialog
        if not ext:
            if "PNG" in returnedFilter or "*.png" in returnedFilter:
                filePath += ".png"
                ext = ".png"
            elif "SVG" in returnedFilter or "*.svg" in returnedFilter:
                filePath += ".svg"
                ext = ".svg"
            elif "TIFF" in returnedFilter or "*.tiff" in returnedFilter:
                filePath += ".tiff"
                ext = ".tiff"
            else:
                # Fall back to radio button selection
                filePath += self._getDefaultExtension()
                ext = os.path.splitext(filePath)[1].lower()

        logger.info(f"Exporting to: {filePath} with extension: {ext}")

        if ext == '.png':
            logger.info("Calling _exportAsPng")
            self._exportAsPng(filePath)
        elif ext == '.svg':
            logger.info("Calling _exportAsSvg")
            self._exportAsSvg(filePath)
        elif ext in ('.tiff', '.tif'):
            logger.info("Calling _exportAsTiff")
            self._exportAsTiff(filePath)
        else:
            # Default to PNG for unknown extensions
            logger.warning(f"Unknown extension '{ext}', defaulting to PNG")
            self._exportAsPng(filePath)

        self.accept()

    def _isPyQtGraphItem(self, plotItem):
        """ Check if the plot item is a PyQtGraph item.
        """
        try:
            import pyqtgraph as pg
            from pyqtgraph.graphicsItems.PlotItem import PlotItem
            # Check for PlotItem (used by line plots and image plots) or GraphicsObject
            return isinstance(plotItem, (PlotItem, pg.GraphicsObject))
        except ImportError:
            return False

    def _exportAsPng(self, filePath):
        """ Export the current visualization as PNG.
        """
        logger.info(f"Exporting to PNG: {filePath}")

        # Try to capture with options first (for image plot inspectors)
        pixmap = self._captureCurrentView()
        if pixmap is not None:
            pixmap.save(filePath, "PNG")
            logger.info(f"Successfully exported PNG to: {filePath}")
            return

        # Fall back to basic plot export
        plotItem = self._getPlotWidget()

        if plotItem is None:
            self._showExportError("No plot item available for export")
            return

        if self._isPyQtGraphItem(plotItem):
            self._exportPyQtGraphAsPng(plotItem, filePath)
        elif isinstance(plotItem, QtWidgets.QWidget):
            self._exportQWidgetAsPng(plotItem, filePath)
        else:
            self._showExportError(f"Unsupported plot item type: {type(plotItem)}")

    def _exportAsSvg(self, filePath):
        """ Export the current visualization as SVG.
        """
        logger.info(f"Exporting to SVG: {filePath}")

        # Try to export with options using the graphics layout widget
        inspector = self._mainWindow.inspector
        options = self._getExportOptions()

        if hasattr(inspector, 'graphicsLayoutWidget'):
            try:
                import pyqtgraph as pg
                import pyqtgraph.exporters

                graphicsWidget = inspector.graphicsLayoutWidget
                originalStates = {}

                # Handle color legend (contains both color scale and histogram)
                if hasattr(inspector, 'colorLegendItem'):
                    colorLegend = inspector.colorLegendItem
                    originalStates['colorLegendVisible'] = colorLegend.isVisible()

                    # Get original histogram state from the inspector's config
                    if hasattr(inspector, 'config') and hasattr(inspector.config, 'showHistCti'):
                        originalStates['histogramVisible'] = inspector.config.showHistCti.configValue
                    else:
                        originalStates['histogramVisible'] = True  # Default assumption

                    # Show color legend if either colorScale or histogram is checked
                    shouldShowColorLegend = options['colorScale'] or options['histogram']
                    colorLegend.setVisible(shouldShowColorLegend)

                    # Control histogram visibility independently
                    if shouldShowColorLegend and hasattr(colorLegend, 'showHistogram'):
                        colorLegend.showHistogram(options['histogram'])

                # Use PyQtGraph's SVGExporter on the central item (GraphicsLayout)
                exporter = pg.exporters.SVGExporter(graphicsWidget.ci)
                exporter.export(filePath)

                # Restore original states
                if hasattr(inspector, 'colorLegendItem'):
                    colorLegend = inspector.colorLegendItem
                    if hasattr(colorLegend, 'showHistogram'):
                        colorLegend.showHistogram(originalStates['histogramVisible'])
                    colorLegend.setVisible(originalStates['colorLegendVisible'])

                logger.info(f"Successfully exported SVG to: {filePath}")
                return
            except Exception as ex:
                logger.warning(f"Failed to export with options, falling back: {ex}")

        # Fall back to basic plot export
        plotItem = self._getPlotWidget()

        if plotItem is None:
            self._showExportError("No plot item available for export")
            return

        isPyQtGraph = self._isPyQtGraphItem(plotItem)
        logger.info(f"Plot item type: {type(plotItem)}, isPyQtGraph: {isPyQtGraph}")

        if isPyQtGraph:
            logger.info("Using PyQtGraph SVG exporter")
            self._exportPyQtGraphAsSvg(plotItem, filePath)
        elif isinstance(plotItem, QtWidgets.QWidget):
            self._exportQWidgetAsSvg(plotItem, filePath)
        else:
            self._showExportError(f"Unsupported plot item type: {type(plotItem)}")

    def _exportAsTiff(self, filePath):
        """ Export the current visualization as TIFF.
        """
        logger.info(f"Exporting to TIFF: {filePath}")

        # Try to capture with options first (for image plot inspectors)
        pixmap = self._captureCurrentView()
        if pixmap is not None:
            pixmap.save(filePath, "TIFF")
            logger.info(f"Successfully exported TIFF to: {filePath}")
            return

        # Fall back to basic plot export
        plotItem = self._getPlotWidget()

        if plotItem is None:
            self._showExportError("No plot item available for export")
            return

        if self._isPyQtGraphItem(plotItem):
            self._exportPyQtGraphAsTiff(plotItem, filePath)
        elif isinstance(plotItem, QtWidgets.QWidget):
            self._exportQWidgetAsTiff(plotItem, filePath)
        else:
            self._showExportError(f"Unsupported plot item type: {type(plotItem)}")

    def _exportPyQtGraphAsPng(self, plotItem, filePath):
        """ Export a PyQtGraph item as PNG.
        """
        try:
            import pyqtgraph as pg
            import pyqtgraph.exporters
            exporter = pg.exporters.ImageExporter(plotItem)
            exporter.export(filePath)
            logger.info(f"Successfully exported PNG to: {filePath}")
        except Exception as ex:
            self._showExportError(f"Failed to export PNG: {ex}")

    def _exportPyQtGraphAsSvg(self, plotItem, filePath):
        """ Export a PyQtGraph item as SVG.
        """
        try:
            import pyqtgraph as pg
            import pyqtgraph.exporters
            logger.info(f"Creating SVGExporter for {type(plotItem)}")
            exporter = pg.exporters.SVGExporter(plotItem)
            logger.info(f"Exporter created: {type(exporter)}, now exporting...")
            exporter.export(filePath)
            logger.info(f"Successfully exported SVG to: {filePath}")
        except Exception as ex:
            logger.exception(f"Failed to export SVG: {ex}")
            self._showExportError(f"Failed to export SVG: {ex}")

    def _exportPyQtGraphAsTiff(self, plotItem, filePath):
        """ Export a PyQtGraph item as TIFF.
            Note: PyQtGraph doesn't have a native TIFF exporter, so we export
            as PNG first and then convert using Qt.
        """
        try:
            import pyqtgraph as pg
            import pyqtgraph.exporters
            exporter = pg.exporters.ImageExporter(plotItem)
            # Get the QImage and save as TIFF
            image = exporter.export(toBytes=True)
            qimage = QtGui.QImage.fromData(image)
            qimage.save(filePath, "TIFF")
            logger.info(f"Successfully exported TIFF to: {filePath}")
        except Exception as ex:
            self._showExportError(f"Failed to export TIFF: {ex}")

    def _exportQWidgetAsPng(self, widget, filePath):
        """ Export a QWidget as PNG.
        """
        try:
            pixmap = widget.grab()
            pixmap.save(filePath, "PNG")
            logger.info(f"Successfully exported PNG to: {filePath}")
        except Exception as ex:
            self._showExportError(f"Failed to export PNG: {ex}")

    def _exportQWidgetAsSvg(self, widget, filePath):
        """ Export a QWidget as SVG.
        """
        try:
            generator = QtSvg.QSvgGenerator()
            generator.setFileName(filePath)
            generator.setSize(widget.size())
            generator.setViewBox(widget.rect())
            widget.render(generator)
            logger.info(f"Successfully exported SVG to: {filePath}")
        except Exception as ex:
            self._showExportError(f"Failed to export SVG: {ex}")

    def _exportQWidgetAsTiff(self, widget, filePath):
        """ Export a QWidget as TIFF.
        """
        try:
            pixmap = widget.grab()
            pixmap.save(filePath, "TIFF")
            logger.info(f"Successfully exported TIFF to: {filePath}")
        except Exception as ex:
            self._showExportError(f"Failed to export TIFF: {ex}")

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
