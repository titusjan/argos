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

""" Repository tree.
"""
from __future__ import print_function

import logging
from argos.qt import QtWidgets, QtGui, QtCore, QtSignal, QtSlot, Qt
from argos.config.groupcti import MainGroupCti
from argos.config.boolcti import BoolCti
from argos.repo.baserti import BaseRti
from argos.repo.registry import globalRtiRegistry
from argos.repo.repotreemodel import RepoTreeModel
from argos.widgets.argostreeview import ArgosTreeView
from argos.widgets.constants import (LEFT_DOCK_WIDTH, COL_NODE_NAME_WIDTH,
                                        COL_SHAPE_WIDTH, COL_ELEM_TYPE_WIDTH,
                                        DOCK_SPACING, DOCK_MARGIN)

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901

class RepoWidget(QtWidgets.QWidget):
    """ Shows the repository. At the moment only the repository tree view.
    """
    def __init__(self, repoTreeModel, collector, parent=None):
        """ Constructor.
            :param parent:
        """
        super(RepoWidget, self).__init__(parent=parent)
        self.repoTreeView = RepoTreeView(repoTreeModel, collector, parent=self)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.addWidget(self.repoTreeView)
        self.mainLayout.setSpacing(DOCK_SPACING)
        self.mainLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)



class RepoTreeView(ArgosTreeView):
    """ Tree widget for browsing the data repository.

        Currently it supports only selecting one item. That is, the current item is always the
        selected item (see notes in ArgosTreeView documentation for details).
    """
    # sigRepoItemChanged parameter is BaseRti or None when no RTI is selected, or the model is empty
    # TODO: implement Noneable(BaseRti) type, or something like that?
    sigRepoItemChanged = QtSignal(object)

    def __init__(self, repoTreeModel, collector, parent=None):
        """ Constructor.

            Maintains a reference to a collector. The repo tree view updates the collector when
            the currentIndex changes.
        """
        super(RepoTreeView, self).__init__(treeModel=repoTreeModel, parent=parent)

        self._collector = collector
        self._config = self._createConfig()

        treeHeader = self.header()
        treeHeader.resizeSection(RepoTreeModel.COL_NODE_NAME, COL_NODE_NAME_WIDTH)
        treeHeader.resizeSection(RepoTreeModel.COL_SHAPE, COL_SHAPE_WIDTH)
        treeHeader.resizeSection(RepoTreeModel.COL_ELEM_TYPE, COL_ELEM_TYPE_WIDTH)
        treeHeader.setStretchLastSection(True)

        headerNames = self.model().horizontalHeaders
        enabled = dict((name, True) for name in headerNames)
        enabled[headerNames[RepoTreeModel.COL_NODE_NAME]] = False # Cannot be unchecked
        checked = dict((name, False) for name in headerNames)
        checked[headerNames[RepoTreeModel.COL_NODE_NAME]] = True
        checked[headerNames[RepoTreeModel.COL_SHAPE]] = False
        checked[headerNames[RepoTreeModel.COL_ELEM_TYPE]] = False
        self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})

        self.setContextMenuPolicy(Qt.DefaultContextMenu) # will call contextMenuEvent
        self.setUniformRowHeights(True)
        #self.setIconSize(QtCore.QSize(16, 16))

        # Add actions
        self.topLevelItemActionGroup = QtWidgets.QActionGroup(self) # TODO: not used anymore?
        self.topLevelItemActionGroup.setExclusive(False)
        self.currentItemActionGroup = QtWidgets.QActionGroup(self)
        self.currentItemActionGroup.setExclusive(False)

        removeFileAction = QtWidgets.QAction("Remove from Tree", self.currentItemActionGroup,
                                         shortcut=QtGui.QKeySequence.Delete,
                                         triggered=self.removeCurrentItem)
        self.addAction(removeFileAction)

        reloadFileAction = QtWidgets.QAction("Reload File", self.currentItemActionGroup,
                                         shortcut=QtGui.QKeySequence.Refresh,   #"Ctrl+R",
                                         triggered=self.reloadFileOfCurrentItem)
        self.addAction(reloadFileAction)

        self.openItemAction = QtWidgets.QAction("Open Item", self,
                                       #shortcut="Ctrl+Shift+C",
                                       triggered=self.openCurrentItem)
        self.addAction(self.openItemAction)

        self.closeItemAction = QtWidgets.QAction("Close Item", self,
                                        #shortcut="Ctrl+C", # Ctrl+C already taken for Copy
                                        triggered=self.closeCurrentItem)
        self.addAction(self.closeItemAction)

        # Connect signals
        selectionModel = self.selectionModel() # need to store reference to prevent crash in PySide
        selectionModel.currentChanged.connect(self.currentItemChanged)

        self.model().sigItemChanged.connect(self.repoTreeItemChanged)


    def finalize(self):
        """ Disconnects signals and frees resources
        """
        self.model().sigItemChanged.disconnect(self.repoTreeItemChanged)

        selectionModel = self.selectionModel() # need to store reference to prevent crash in PySide
        selectionModel.currentChanged.disconnect(self.currentItemChanged)


    def contextMenuEvent(self, event):
        """ Creates and executes the context menu for the tree view
        """
        menu = QtWidgets.QMenu(self)

        for action in self.actions():
            menu.addAction(action)

        openAsMenu = self.createOpenAsMenu(parent=menu)
        menu.insertMenu(self.closeItemAction, openAsMenu)

        menu.exec_(event.globalPos())


    def createOpenAsMenu(self, parent=None):
        """ Creates the submenu for the Open As choice
        """
        openAsMenu = QtWidgets.QMenu(parent=parent)
        openAsMenu.setTitle("Open Item As")

        registry = globalRtiRegistry()
        for rtiRegItem in registry.items:
            #rtiRegItem.tryImportClass()
            def createTrigger():
                """Function to create a closure with the regItem"""
                _rtiRegItem = rtiRegItem # keep reference in closure
                return lambda: self.reloadFileOfCurrentItem(_rtiRegItem)

            action = QtWidgets.QAction("{}".format(rtiRegItem.name), self,
                enabled=bool(rtiRegItem.successfullyImported is not False),
                triggered=createTrigger())
            openAsMenu.addAction(action)

        return openAsMenu


    @property
    def config(self):
        """ The root config tree item for this widget
        """
        return self._config


    def _createConfig(self):
        """ Creates a config tree item (CTI) hierarchy containing default children.
        """
        # Currently not added to the config tree as there are no configurable items.
        rootItem = MainGroupCti('data repository')
        rootItem.insertChild(BoolCti('test checkbox', False)) # Does nothing yet
        return rootItem


    @property
    def collector(self): # TODO: move to selector class in the future
        """ The collector that this selector view will update. Read only property.
        """
        return self._collector


    def sizeHint(self):
        """ The recommended size for the widget."""
        return QtCore.QSize(LEFT_DOCK_WIDTH, 450)


    @QtSlot()
    def openCurrentItem(self):
        """ Opens the current item in the repository.
        """
        logger.debug("openCurrentItem")
        _currentItem, currentIndex = self.getCurrentItem()
        if not currentIndex.isValid():
            return

        # Expanding the node will call indirectly call RepoTreeModel.fetchMore which will call
        # BaseRti.fetchChildren, which will call BaseRti.open and thus open the current RTI.
        # BaseRti.open will emit the self.model.sigItemChanged signal, which is connected to
        # RepoTreeView.onItemChanged.
        self.expand(currentIndex)


    @QtSlot()
    def closeCurrentItem(self):
        """ Closes the current item in the repository.
            All its children will be unfetched and closed.
        """
        logger.debug("closeCurrentItem")
        currentItem, currentIndex = self.getCurrentItem()
        if not currentIndex.isValid():
            return

        # First we remove all the children, this will close them as well.
        self.model().removeAllChildrenAtIndex(currentIndex)

        # Close the current item. BaseRti.close will emit the self.model.sigItemChanged signal,
        # which is connected to RepoTreeView.onItemChanged.
        currentItem.close()
        self.dataChanged(currentIndex, currentIndex)
        self.collapse(currentIndex) # otherwise the children will be fetched immediately
                                    # Note that this will happen anyway if the item is open in
                                    # in another view (TODO: what to do about this?)


    # @QtSlot()
    # def __not_used__removeCurrentFile(self):
    #     """ Finds the root of of the current item, which represents a file,
    #         and removes it from the list.
    #     """
    #     logger.debug("removeCurrentFile")
    #     currentIndex = self.getRowCurrentIndex()
    #     if not currentIndex.isValid():
    #         return
    #
    #     topLevelIndex = self.model().findTopLevelItemIndex(currentIndex)
    #     self.model().deleteItemAtIndex(topLevelIndex) # this will close the items resources.


    @QtSlot()
    def removeCurrentItem(self):
        """ Removes the current item from the repository tree.
        """
        logger.debug("removeCurrentFile")
        currentIndex = self.getRowCurrentIndex()
        if not currentIndex.isValid():
            return

        self.model().deleteItemAtIndex(currentIndex) # this will close the items resources.


    @QtSlot()
    def reloadFileOfCurrentItem(self, rtiRegItem=None):
        """ Finds the repo tree item that holds the file of the current item and reloads it.
            Reloading is done by removing the repo tree item and inserting a new one.

            The new item will have by of type rtiRegItem.cls. If rtiRegItem is None (the default),
            the new rtiClass will be the same as the old one.
            The rtiRegItem.cls will be imported. If this fails the old class will be used, and a
            warning will be logged.
        """
        logger.debug("reloadFileOfCurrentItem, rtiClass={}".format(rtiRegItem))


        currentIndex = self.getRowCurrentIndex()
        if not currentIndex.isValid():
            return

        currentItem, _ = self.getCurrentItem()
        oldPath = currentItem.nodePath

        fileRtiIndex = self.model().findFileRtiIndex(currentIndex)
        isExpanded = self.isExpanded(fileRtiIndex)

        if rtiRegItem is None:
            rtiClass = None
        else:
            rtiRegItem.tryImportClass()
            rtiClass = rtiRegItem.cls

        newRtiIndex = self.model().reloadFileAtIndex(fileRtiIndex, rtiClass=rtiClass)

        try:
            # Expand and select the name with the old path
            _lastItem, lastIndex = self.expandPath(oldPath)
            self.setCurrentIndex(lastIndex)
            return lastIndex
        except Exception as ex:
            # The old path may not exist anymore. In that case select file RTI
            logger.warning("Unable to select {!r} beause of: {}".format(oldPath, ex))
            self.setExpanded(newRtiIndex, isExpanded)
            self.setCurrentIndex(newRtiIndex)
            return newRtiIndex


    @QtSlot(QtCore.QModelIndex)
    @QtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def currentItemChanged(self, currentIndex, _previousIndex=None):
        """ Enables/disables actions when a new item is the current item in the tree view.

            Is not called currentChanged as this would override an existing method. We want to
            connect this to the currentChanged signal at the end of the constructor, which would
            then not be possible.
        """
        self.currentRepoTreeItemChanged()


    def repoTreeItemChanged(self, rti):
        """ Called when repo tree item has changed (the item itself, not a new selection)

            If the item is the currently selected item, the the collector (inspector) and
            metadata widgets are updated.
        """
        logger.debug("onItemChanged: {}".format(rti))
        currentItem, _currentIndex = self.getCurrentItem()

        if rti == currentItem:
            self.currentRepoTreeItemChanged()
        else:
            logger.debug("Ignoring changed item as is not the current item: {}".format(rti))


    def currentRepoTreeItemChanged(self):
        """ Called to update the GUI when a repo tree item has changed or a new one was selected.
        """
        # When the model is empty the current index may be invalid and the currentItem may be None.
        currentItem, currentIndex = self.getCurrentItem()

        hasCurrent = currentIndex.isValid()
        assert hasCurrent == (currentItem is not None), \
            "If current idex is valid, currentIndex may not be None" # sanity check

        # Set the item in the collector, will will subsequently update the inspector.
        if hasCurrent:
            logger.info("Adding rti to collector: {}".format(currentItem.nodePath))
            self.collector.setRti(currentItem)
            #if rti.asArray is not None: # TODO: maybe later, first test how robust it is now
            #    self.collector.setRti(rti)

        # Update context menus in the repo tree
        self.currentItemActionGroup.setEnabled(hasCurrent)
        isTopLevel = hasCurrent and self.model().isTopLevelIndex(currentIndex)
        self.topLevelItemActionGroup.setEnabled(isTopLevel)
        self.openItemAction.setEnabled(currentItem is not None
                                       and currentItem.hasChildren()
                                       and not currentItem.isOpen)
        self.closeItemAction.setEnabled(currentItem is not None
                                        and currentItem.hasChildren()
                                        and currentItem.isOpen)

        # Emit sigRepoItemChanged signal so that, for example, details panes can update.
        logger.debug("Emitting sigRepoItemChanged: {}".format(currentItem))
        self.sigRepoItemChanged.emit(currentItem)
