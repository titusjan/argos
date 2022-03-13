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

""" Contains the TestWalkDialog widget.
"""
import logging
import time
from typing import Optional, Tuple, List

from argos.qt import QtCore, QtGui, QtWidgets, QtSlot
from argos.widgets.constants import MONO_FONT, FONT_SIZE
from argos.widgets.misc import processEvents
from argos.utils.cls import check_is_a_sequence

logger = logging.getLogger(__name__)


# The main window inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201


class TestWalkDialog(QtWidgets.QDialog):
    """ Dialog that shows progress of test walk through the data and gives a summary when done.
    """
    def __init__(self, mainWindow, parent=None):
        """ Constructor

            Args:
                mainWindow: the Argos main window.
        """
        super(TestWalkDialog, self).__init__(parent=parent)
        self.setModal(False)

        self._mainWindow = mainWindow

        self._currentTestName: Optional[str] = None
        self._results: List[Tuple[bool, str]] = []

        mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(mainLayout)

        self.curPathLabel = QtWidgets.QLabel()
        self.curPathLabel.setText("Current Path")
        self.curPathLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        mainLayout.addWidget(self.curPathLabel)

        font = QtGui.QFont()
        font.setFamily(MONO_FONT)
        font.setFixedPitch(True)
        font.setPointSize(FONT_SIZE)

        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setFont(font)
        self.editor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.editor.clear()
        mainLayout.addWidget(self.editor)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)
        mainLayout.addWidget(buttonBox)

        self.resize(QtCore.QSize(800, 400))


    def clear(self):
        """ Clear all test results and current test name.
        """
        self._currentTestName = None
        self._results = None
        self.editor.clear()

    #
    # def getCurrentTestName(self, currentTestName: str):
    #     """ Returns name of the current test.
    #     """
    #     self._currentTestName = currentTestName
    #
    #
    # def setCurrentTestName(self, currentTestName: str):
    #     """ Stores name of the current test.
    #     """
    #     self._currentTestName = currentTestName


    def testOngoing(self) -> bool:
        """ Returns True if a test is ongoing
        """
        return bool(self._currentTestName)


    @QtSlot(bool)
    def setTestResult(self, success: bool):
        """ Appends the currently selected path node to the list of tests.

            This slot will be called whenever the inspector or detail tab (properties, attributes,
            quicklook) updates itself.

            Setting the name and result are separate methods because the inspector and detail tab
            don't know which node is currently selected in the repo tree.
        """
        if not self.testOngoing():
            return

        self._results.append((success, self._currentTestName))

        line = "{:7s}: {}".format("success" if success else "FAILED", self._currentTestName)
        logger.info("setTestResult: {}".format(line))
        self.editor.appendPlainText(line)


    def walkCurrentRepoNode(self, allInspectors: bool, allRepoTabs: bool):
        """ Will visit all nodes below the currently selected node
        """
        curItem, _curIdx = self._mainWindow.repoWidget.repoTreeView.getCurrentItem()
        logger.debug("CurrentItem: {}".format(curItem.nodePath))
        self.walkRepoNodes([curItem.nodePath], allInspectors, allRepoTabs)


    def walkAllRepoNodes(self, allInspectors: bool, allRepoTabs: bool):
        """ Will visit all nodes in the repo tree.

            See walkRepoNodes docstring for more info
        """
        logger.info("testWalkAllNodes")
        repo = self._mainWindow.repoWidget.repoTreeView.model()
        nodePaths = [rti.nodePath for rti in repo.rootItems()]
        logger.debug("All root items: {}".format(nodePaths))
        self.walkRepoNodes(nodePaths, allInspectors, allRepoTabs)


    def walkRepoNodes(self, nodePaths, allInspectors: bool, allDetailsTabs: bool):
        """ Will recursively walk through a list of repo tree nodes and all their descendants

            Is useful for testing.

            Args:
                allInspectors: if True all inspectors are tried for this node.
                allDetailsTabs: if True all detail tabs (attributes, quicklook, etc.) are tried.
        """
        # TODO: detail tabs must signal when they fail
        # TODO: skip tests starting with underscore
        # TODO: test walk dialog with progress bar and cancel button
        # TODO: select original node at the end of the tests.
        # TODO: separate test menu

        logger.info("-------------- Running Tests ----------------")
        logger.debug("Visiting all nodes below: {}".format(nodePaths))

        self.show()
        self._currentTestName = None
        self._results = []
        self.editor.clear()
        nodesVisited = 0

        try:
            timeAtStart = time.perf_counter()
            check_is_a_sequence(nodePaths) # prevent accidental iteration over strings.

            for nodePath in nodePaths:
                nodeItem, nodeIndex = self._mainWindow.selectRtiByPath(nodePath)
                assert nodeItem is not None, "Test data not found, rootNode: {}".format(nodePath)
                assert nodeIndex

                nodesVisited += self._visitNodes(nodeIndex, allInspectors, allDetailsTabs)

            duration = time.perf_counter() - timeAtStart
            self._logTestSummary(duration, nodesVisited)
        finally:
            self._currentTestName = None
            self._results = []
            logger.info("-------------- Test walk done ----------------")


    def _visitNodes(self, index: QtCore.QModelIndex, allInspectors: bool, allDetailTabs: bool) -> int:
        """ Helper function that visits all the nodes recursively.

            Args:
                allInspectors: if True all inspectors are tried for this node.
                allDetailsTabs: if True all detail tabs (attributes, quicklook, etc.) are tried.

            Returns:
                The number of nodes that where visited.
        """
        assert index.isValid(), "sanity check"

        nodesVisited = 1

        repoWidget = self._mainWindow.repoWidget
        repoModel = repoWidget.repoTreeView.model()

        item = repoModel.getItem(index)
        logger.info("Visiting: {!r} ({} children)".
                    format(item.nodePath, repoModel.rowCount(index)))

        # Select index
        if False and item.nodePath in skipPaths:
            logger.warning("Skipping node during testing: {}".format(item.nodePath))
            return 0
        else:
            logger.debug("Not skipping node during testing: {}".format(item.nodePath))

        repoWidget.repoTreeView.setCurrentIndex(index)
        repoWidget.repoTreeView.setExpanded(index, True)

        if allDetailTabs:
            # Try properties, attributes and quicklook tabs
            for idx in range(repoWidget.tabWidget.count()):
                tabName = repoWidget.tabWidget.tabText(idx)
                self._currentTestName = "{:10}: {}".format(tabName, item.nodePath)
                logger.debug("Setting repo detail tab : {}".format(tabName))
                repoWidget.tabWidget.setCurrentIndex(idx)
                processEvents() # Cause Qt to update UI
        else:
            self._currentTestName = item.nodePath
            processEvents()

        if allInspectors:
            for action in self._mainWindow.inspectorActionGroup.actions():
                self._currentTestName = "{:10}: {}".format(action.text(), item.nodePath)
                action.trigger()
                processEvents() # Cause Qt to update UI
        else:
            self._currentTestName = item.nodePath
            processEvents()

        for rowNr in range(repoModel.rowCount(index)):
            childIndex = repoModel.index(rowNr, 0, parentIndex=index)
            nodesVisited += self._visitNodes(childIndex, allInspectors, allDetailTabs)

        # TODO: see if we can close the node
        return nodesVisited


    def _logTestSummary(self, duration: float, nodesVisited: int):
        """ Logs a summary of the test results.
        """
        logger.info("Visited {} nodes in {:.1f} seconds ({:.1f} nodes/second)."
                    .format(nodesVisited, duration, nodesVisited/duration))

        failedTests = [(success, name) for success, name in self._results if not success]
        failedTests = self._results
        logger.info("Number of failed tests during test walk: {}".format(len(failedTests)))
        for testName in failedTests:
            logger.info("    {}".format(testName))
