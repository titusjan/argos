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

""" Base class for inspectors
"""
import logging

from argos.info import DEBUGGING
from argos.qt import QtSlot, QtCore, QtWidgets
from argos.qt.togglecolumn import ToggleColumnTableWidget
from argos.repo.baserti import BaseRti
from argos.utils.cls import get_class_name, check_class
from argos.widgets.constants import DOCK_SPACING, DOCK_MARGIN, LEFT_DOCK_WIDTH
from argos.widgets.display import MessageDisplay

logger = logging.getLogger(__name__)



class DetailBasePane(QtWidgets.QStackedWidget):
    """ Base class for plugins that show details of the current repository tree item.
        Serves as an interface but can also be instantiated for debugging purposes.
        A detail pane is a stacked widget; it has a contents page and and error page.
    """
    _label = "Details"

    ERROR_PAGE_IDX = 0
    CONTENTS_PAGE_IDX = 1

    def __init__(self, repoTreeView, parent=None):
        """ Constructor takes a reference to the repository tree view it monitors
        """
        super(DetailBasePane, self).__init__(parent)

        self._isConnected = False
        self._repoTreeView = repoTreeView

        self.errorWidget = MessageDisplay()
        self.addWidget(self.errorWidget)

        self.contentsWidget = QtWidgets.QWidget()
        self.addWidget(self.contentsWidget)

        self.contentsLayout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom)
        self.contentsLayout.setSpacing(DOCK_SPACING)
        self.contentsLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)
        self.contentsWidget.setLayout(self.contentsLayout)

        self.setCurrentIndex(self.CONTENTS_PAGE_IDX)


    @classmethod
    def classLabel(cls):
        """ Returns a short string that describes this class. For use in menus, headers, etc.
        """
        return cls._label


    @property
    def isConnected(self):
        "Returns True if this pane is connected to the currentChanged signal of the repoTreeView"
        return self._isConnected


    def sizeHint(self):
        """ The recommended size for the widget."""
        return QtCore.QSize(LEFT_DOCK_WIDTH, 250)


    @QtSlot(bool)
    def dockVisibilityChanged(self, visible):
        """ Slot to be called when the dock widget that this pane contains become (in)visible.
            Is used to (dis)connect the pane from its repo tree view and so prevent unnecessary
            and potentially costly updates when the pane is hidden.
        """
        logger.debug("dockVisibilityChanged of {!r}: visible={}".format(self, visible))

        if visible:
            self._repoTreeView.sigRepoItemChanged.connect(self.repoItemChanged)
            self._isConnected = True

            currentRepoItem, _currentIndex = self._repoTreeView.getCurrentItem()
            self.repoItemChanged(currentRepoItem)
        else:
            # At start-up the pane be be hidden but the signals are not connected.
            # A disconnect would fail in that case so we test for isConnected == True.
            if self.isConnected:
                self._repoTreeView.sigRepoItemChanged.disconnect(self.repoItemChanged)

            self._isConnected = False
            self.errorWidget.setError(msg="Contents disabled", title="Error")
            self.setCurrentIndex(self.ERROR_PAGE_IDX)


    def repoItemChanged(self, rti):
        """ Updates the content when the current repo tree item changes.
            The rti parameter can be None when no RTI is selected in the repository tree.
        """
        check_class(rti, (BaseRti, int), allow_none=True)
        assert type(rti) != int, "rti: {}".format(rti)
        try:
            self._drawContents(rti)
            self.setCurrentIndex(self.CONTENTS_PAGE_IDX)
        except Exception as ex:
            if DEBUGGING:
                raise
            logger.exception(ex)
            self.errorWidget.setError(msg=str(ex), title=get_class_name(ex))
            self.setCurrentIndex(self.ERROR_PAGE_IDX)


    def _drawContents(self, currentRti=None):
        """ Draws the contents for the current RTI. Descendants should override this.
            Descendants should draw 'empty' contents if currentRti is None. No need to
            handle exceptions though, these are handled by the called (currentChanged).
        """
        pass



class DetailTablePane(DetailBasePane):
    """ Base class for inspectors that consist of a single QTableWidget
    """
    _label = "Details Table"

    HEADERS = [] # Children should override this

    def __init__(self, repoTreeView, parent=None):
        super(DetailTablePane, self).__init__(repoTreeView, parent=parent)

        self.table = ToggleColumnTableWidget()
        self.contentsLayout.addWidget(self.table)

        self.table.setWordWrap(False)
        #self.table.setTextElideMode(QtCore.Qt.ElideNone)
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)

        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        tableHeader = self.table.horizontalHeader()
        tableHeader.setSectionResizeMode(QtWidgets.QHeaderView.Interactive) # don't set to stretch
        tableHeader.setStretchLastSection(True)

