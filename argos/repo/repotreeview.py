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
from argos.repo.detailplugins.attr import AttributesPane
from argos.repo.detailplugins.prop import PropertiesPane
from argos.repo.detailplugins.quicklook import QuickLookPane
from argos.repo.registry import globalRtiRegistry
from argos.repo.repotreemodel import RepoTreeModel
from argos.widgets.argostreeview import ArgosTreeView
from argos.widgets.constants import LEFT_DOCK_WIDTH, DOCK_SPACING, DOCK_MARGIN, COL_KIND_WIDTH
from argos.widgets.constants import COL_NODE_NAME_WIDTH, COL_ELEM_TYPE_WIDTH, COL_SUMMARY_WIDTH

from argos.widgets.misc import BasePanel


logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901



class RepoWidget(BasePanel):
    """ Groups the repository tree plus the details dock widgets.
    """
    def __init__(self, repoTreeModel, collector, parent=None):
        """ Constructor.
            :param parent:
        """
        super(RepoWidget, self).__init__(parent=parent)

        self.detailDockPanes = []

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setSpacing(DOCK_SPACING)
        self.mainLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)
        self.setLayout(self.mainLayout)

        self.mainSplitter = QtWidgets.QSplitter(orientation=Qt.Vertical)
        self.mainLayout.addWidget(self.mainSplitter)

        self.repoTreeView = RepoTreeView(repoTreeModel, collector)
        self.mainSplitter.addWidget(self.repoTreeView)
        self.mainSplitter.setCollapsible(0, False)

        self.tabWidget = QtWidgets.QTabWidget()
        self.mainSplitter.addWidget(self.tabWidget)
        self.mainSplitter.setCollapsible(1, True)

        self.propertiesPane = self.addDetailsPane(PropertiesPane(self.repoTreeView))
        self.attributesPane = self.addDetailsPane(AttributesPane(self.repoTreeView))
        self.quickLookPane = self.addDetailsPane(QuickLookPane(self.repoTreeView))

        self.repoTreeView.sigRepoItemChanged.connect(self.repoItemChanged)
        self.tabWidget.currentChanged.connect(self.tabChanged)

        self.tabWidget.setCurrentIndex(2) # Show quick look tab the first time the program runs



    def addDetailsPane(self, detailPane):
        """ Adds a pane widget as a tab.

            Returns: detailPane so calls can be chained.
        """
        self.tabWidget.addTab(detailPane, detailPane.classLabel())
        self.detailDockPanes.append(detailPane)
        return detailPane


    def marshall(self):
        """ Returns a dictionary to save in the persistent settings
        """
        cfg = dict(
            tabIndex = self.tabWidget.currentIndex(),
            splitterSizes = self.mainSplitter.sizes(),
            treeHeaders = self.repoTreeView.marshall(),
            propertiesPane = self.propertiesPane.marshall(),
            attributesPane = self.attributesPane.marshall(),
        )

        return cfg


    def unmarshall(self, cfg):
        """ Initializes itself from a config dict form the persistent settings.
        """
        if 'tabIndex' in cfg:
            self.tabWidget.setCurrentIndex(cfg['tabIndex'])

        if 'splitterSizes' in cfg:
            self.mainSplitter.setSizes(cfg['splitterSizes'])

        self.repoTreeView.unmarshall(cfg.get('treeHeaders'))

        self.propertiesPane.unmarshall(cfg.get('propertiesPane', {}))
        self.attributesPane.unmarshall(cfg.get('attributesPane', {}))


    def repoItemChanged(self, rti):
        """ Updates the current tab with the newly selected repoWidget

            The rti parameter can be None when no RTI is selected in the repository tree.
        """
        logger.debug("RepoWidget.repoItemChanged: {}".format(rti))

        curPanel = self.tabWidget.currentWidget() # can be None according to docs
        if curPanel:
            curPanel.repoItemChanged(rti)
        else:
            logger.debug("No panel selected")


    def tabChanged(self, _tabIndex):
        """ Updates the tab from the currently selected repo item in the tree.
        """
        currentRepoItem, _currentIndex = self.repoTreeView.getCurrentItem()
        self.repoItemChanged(currentRepoItem)



class RepoTreeView(ArgosTreeView):
    """ Tree widget for browsing the data repository.

        Currently it supports only selecting one item. That is, the current item is always the
        selected item (see notes in ArgosTreeView documentation for details).
    """
    # sigRepoItemChanged parameter is BaseRti or None when no RTI is selected, or the model is empty
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
        treeHeader.resizeSection(RepoTreeModel.COL_KIND, COL_KIND_WIDTH)
        treeHeader.resizeSection(RepoTreeModel.COL_ELEM_TYPE, COL_ELEM_TYPE_WIDTH)
        treeHeader.resizeSection(RepoTreeModel.COL_SUMMARY, COL_SUMMARY_WIDTH)

        # Note: this setting is stored in the json file. Remove the config file if you want to
        # change it.
        treeHeader.setStretchLastSection(True)

        headerNames = self.model().horizontalHeaders
        enabled = dict((name, True) for name in headerNames)
        enabled[headerNames[RepoTreeModel.COL_NODE_NAME]] = False # Cannot be unchecked
        checked = dict((name, False) for name in headerNames)
        checked[headerNames[RepoTreeModel.COL_NODE_NAME]] = True
        checked[headerNames[RepoTreeModel.COL_KIND]] = True
        checked[headerNames[RepoTreeModel.COL_ELEM_TYPE]] = True
        checked[headerNames[RepoTreeModel.COL_SUMMARY]] = True
        self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})

        self.setContextMenuPolicy(Qt.DefaultContextMenu) # will call contextMenuEvent
        self.setUniformRowHeights(True)
        #self.setIconSize(QtCore.QSize(16, 16))

        # Add actions
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

        self.openItemAction = QtWidgets.QAction("Open Item", self, triggered=self.openCurrentItem)
        self.addAction(self.openItemAction)

        self.closeItemAction = QtWidgets.QAction("Close Item", self, triggered=self.closeCurrentItem)
        self.addAction(self.closeItemAction)

        self.collapseItemAction = QtWidgets.QAction("Collapse Item", self, triggered=self.collapseCurrentItem)
        self.addAction(self.collapseItemAction)

        self.copyPathAction = QtWidgets.QAction("Copy Path to Clipboard", self,
                                                triggered=self.copyPathToClipboard)
        self.addAction(self.copyPathAction)

        # Connect signals
        selectionModel = self.selectionModel() # need to store reference to prevent crash in PySide
        selectionModel.currentChanged.connect(self.currentItemChanged)

        # Close files on collapse. Note that, self.collapsed does NOT seem to be connected to self.collapse by default,
        # so there is not conflict here. Also there is no need to connect to expand, this is automatic with the
        # fetchMore mechanism
        self.collapsed.connect(self.closeItem)

        self.model().sigItemChanged.connect(self.repoTreeItemChanged)
        self.model().sigAllChildrenRemovedAtIndex.connect(self.collapse)


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

        openAsMenu = QtWidgets.QMenu(parent=menu)
        openAsMenu.setTitle("Open Item As")
        openAsMenu.aboutToShow.connect(lambda :self._populateOpenAsMenu(openAsMenu))
        menu.insertMenu(self.closeItemAction, openAsMenu) # Insert before "Close Item" entry.

        menu.exec_(event.globalPos())


    def _populateOpenAsMenu(self, openAsMenu):
        """ Repopulates the submenu for the Open Item choice (which is used to reload files).
        """
        registry = globalRtiRegistry()
        for rtiRegItem in (registry.items + registry.extraItemsForOpenAsMenu()):

            if not rtiRegItem.triedImport:
                rtiRegItem.tryImportClass()

            def createTrigger():
                """Function to create a closure with the regItem"""
                _rtiRegItem = rtiRegItem # keep reference in closure
                return lambda: self.reloadFileOfCurrentItem(_rtiRegItem)

            action = QtWidgets.QAction("{}".format(rtiRegItem.name), self,
                enabled=bool(rtiRegItem.successfullyImported is not False),
                triggered=createTrigger(), icon=rtiRegItem.decoration)
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
    def copyPathToClipboard(self):
        """ Copies the path of the currently selected item to the clipboard
        """
        currentItem, currentIndex = self.getCurrentItem()
        if not currentIndex.isValid():
            return

        QtWidgets.QApplication.clipboard().setText(currentItem.nodePath)
        logger.info("Copied path to the clipboard: {}".format(currentItem.nodePath))



    @QtSlot()
    def openCurrentItem(self):
        """ Opens the current item in the repository.
        """
        logger.debug("openCurrentItem called")
        _currentItem, currentIndex = self.getCurrentItem()
        if not currentIndex.isValid():
            return

        # Expanding the node will indirectly call RepoTreeModel.fetchMore which will call
        # BaseRti.fetchChildren, which will call BaseRti.open and thus open the current RTI.
        # BaseRti.open will emit the self.model.sigItemChanged signal, which is connected to
        # RepoTreeView.repoTreeItemChanged.
        self.expand(currentIndex)


    @QtSlot()
    def closeCurrentItem(self):
        """ Closes the current item in the repository.
            All its children will be unfetched and closed.
        """
        self.closeItem(self.getRowCurrentIndex())


    @QtSlot(QtCore.QModelIndex)
    def closeItem(self, index):
        """ Closes the item at the index and collapses the node
        """
        logger.debug("closeItem called")
        if not index.isValid():
            logger.debug("Index invalid (returning)")
            return

        # First we remove all the children, this will close them as well.
        # It will emit sigAllChildrenRemovedAtIndex, which is connected to the collapse method of
        # all trees. It will thus collapse the current item in all trees. This is necessary,
        # otherwise the children will be fetched immediately.
        self.model().removeAllChildrenAtIndex(index)

        # Close the item. BaseRti.close will emit the self.model.sigItemChanged signal,
        # which is connected to RepoTreeView.repoTreeItemChanged.
        item = self.model().getItem(index)
        logger.debug("Item: {}".format(item))
        item.close()


    def expand(self, index):
        """ Expands current item. Updates context menu action.
        """
        super(RepoTreeView, self).expand(index)
        self.collapseItemAction.setEnabled(self.isExpanded(index))


    def collapse(self, index):
        """ Collapses current item. Updates context menu action.
        """
        super(RepoTreeView, self).collapse(index)
        self.collapseItemAction.setEnabled(self.isExpanded(index))


    @QtSlot()
    def collapseCurrentItem(self):
        """ Closes the current item in the repository.
            All its children will be unfetched and closed.
        """
        currentIndex = self.getRowCurrentIndex()
        oldBlockState = self.blockSignals(True)  # Prevent automatically closing of item.
        try:
            self.collapse(currentIndex)
        finally:
            self.blockSignals(oldBlockState)


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

        newRtiIndex = self.model().reloadFileAtIndex(fileRtiIndex, rtiRegItem=rtiRegItem)

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

            If the item is the currently selected item, the collector (inspector) and
            metadata widgets are updated.
        """
        logger.debug("repoTreeItemChanged: {}".format(rti))
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
            "If current index is valid, currentIndex may not be None" # sanity check

        # Set the item in the collector, will subsequently update the inspector.
        if hasCurrent:
            logger.debug("Adding rti to collector: {}".format(currentItem.nodePath))
            self.collector.setRti(currentItem)
            #if rti.asArray is not None: # TODO: maybe later, first test how robust it is now
            #    self.collector.setRti(rti)

        # Update context menus in the repo tree
        self.currentItemActionGroup.setEnabled(hasCurrent)
        isTopLevel = hasCurrent and self.model().isTopLevelIndex(currentIndex)
        self.collapseItemAction.setEnabled(self.isExpanded(currentIndex))
        self.openItemAction.setEnabled(currentItem is not None
                                       and currentItem.hasChildren()
                                       and not currentItem.isOpen)
        self.closeItemAction.setEnabled(currentItem is not None
                                        and currentItem.hasChildren()
                                        and currentItem.isOpen)

        # Emit sigRepoItemChanged signal so that, for example, details panes can update.
        logger.debug("Emitting sigRepoItemChanged: {}".format(currentItem))
        self.sigRepoItemChanged.emit(currentItem)
