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
import base64
import copy
import logging
import time
from typing import Optional, Tuple, List

from argos.qt import Qt, QtCore, QtGui, QtWidgets, QtSlot
from argos.qt.misc import getWidgetGeom, getWidgetState
from argos.widgets.constants import MONO_FONT, FONT_SIZE, COLOR_ERROR
from argos.widgets.misc import processEvents
from argos.utils.cls import check_is_a_sequence
from argos.utils.config import ConfigDict
from argos.utils.misc import wrapHtmlColor

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

        self._isOngoing = False
        self._showAllResults = False

        self._mainWindow = mainWindow

        self._currentTestName: Optional[str] = None
        self._results: List[Tuple[bool, str]] = []

        self.walkCurrentAction = QtWidgets.QAction("Walk Current Item", self)
        self.walkCurrentAction.setToolTip("Does a test walk on the currently selected tree item.")
        self.walkCurrentAction.triggered.connect(self.walkCurrentRepoNode)
        self.addAction(self.walkCurrentAction)

        self.walkAllAction = QtWidgets.QAction("Walk All Items", self)
        self.walkAllAction.setToolTip("Does a test walk on all tree nodes.")
        self.walkAllAction.triggered.connect(self.walkAllRepoNodes)
        self.addAction(self.walkAllAction)

        self.abortWalkAction = QtWidgets.QAction("Abort Walk", self)
        self.abortWalkAction.setToolTip("Aborts the current test walk.")
        self.abortWalkAction.triggered.connect(self.abortTestWalk)
        self.addAction(self.abortWalkAction)

        #################
        # Setup widgets #
        #################

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.controlLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addLayout(self.controlLayout)

        self.walkCurrentButton = QtWidgets.QToolButton()
        self.walkCurrentButton.setDefaultAction(self.walkCurrentAction)
        self.controlLayout.addWidget(self.walkCurrentButton)

        self.walkAllButton = QtWidgets.QToolButton()
        self.walkAllButton.setDefaultAction(self.walkAllAction)
        self.controlLayout.addWidget(self.walkAllButton)

        self.abortWalkButton = QtWidgets.QToolButton()
        self.abortWalkButton.setDefaultAction(self.abortWalkAction)
        self.controlLayout.addWidget(self.abortWalkButton)

        self.allInspectorsCheckBox = QtWidgets.QCheckBox("Test all Inspectors")
        self.controlLayout.addWidget(self.allInspectorsCheckBox)
        self.allDetailTabsCheckBox = QtWidgets.QCheckBox("Test all Detail-tabs")
        self.controlLayout.addWidget(self.allDetailTabsCheckBox)
        self.controlLayout.addStretch()

        self.progressBar = QtWidgets.QProgressBar()
        self.mainLayout.addWidget(self.progressBar)

        self.curPathLabel = QtWidgets.QLabel()
        self.curPathLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.mainLayout.addWidget(self.curPathLabel)

        font = QtGui.QFont()
        font.setFamily(MONO_FONT)
        font.setFixedPitch(True)
        font.setPointSize(FONT_SIZE)

        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setFont(font)
        self.editor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.editor.clear()
        self.mainLayout.addWidget(self.editor)

        self.bottomLayout = QtWidgets.QHBoxLayout()
        self.bottomLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addLayout(self.bottomLayout)

        self.showAllResCheckBox = QtWidgets.QCheckBox("Show all results")
        self.showAllResCheckBox.stateChanged.connect(self.onShowAllResultsChanged)
        self.bottomLayout.addWidget(self.showAllResCheckBox)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        self.bottomLayout.addWidget(buttonBox)

        self.resize(QtCore.QSize(800, 400))
        self._updateButtons()


    def finalize(self):
        """ Is called before destruction (when closing).
            Can be used to clean-up resources.
        """
        self.showAllResCheckBox.stateChanged.disconnect(self.onShowAllResultsChanged)


    @property
    def results(self):
        """ Get a copy of the test results
        """
        return copy.deepcopy(self._results)


    @property
    def repoWidget(self):
        """ The repoWidget of the main window
        """
        return self._mainWindow.repoWidget


    @property
    def repoTreeView(self):
        """ The repoTreeView of repo widget of the main window
        """
        return self._mainWindow.repoWidget.repoTreeView


    def marshall(self) -> Tuple[ConfigDict, ConfigDict]:
        """ Returns a layout and state config dictionaries
        """
        layoutCfg = dict(
            winGeom = base64.b64encode(getWidgetGeom(self)).decode('ascii'),
        )

        cfg = dict(
            testAllInspectors = self.allInspectorsCheckBox.isChecked(),
            testAllDetailTabs = self.allDetailTabsCheckBox.isChecked(),
            showAllResults = self.showAllResCheckBox.isChecked(),
        )
        return layoutCfg, cfg


    def unmarshall(self, layoutCfg, cfg):
        """ Initializes itself from a layout and config dict form the persistent settings.
        """
        if 'testAllInspectors' in cfg:
            self.allInspectorsCheckBox.setChecked(cfg['testAllInspectors'])

        if 'testAllDetailTabs' in cfg:
            self.allDetailTabsCheckBox.setChecked(cfg['testAllDetailTabs'])

        if 'showAllResults' in cfg:
            self.showAllResCheckBox.setChecked(cfg['showAllResults'])

        if 'winGeom' in layoutCfg:
            self.restoreGeometry(base64.b64decode(layoutCfg['winGeom']))


    def reject(self):
        """ Called when the user closes the dialog. Aborts any running test walk.
        """
        logger.debug("Closing TestWalkDialog")
        self.abortTestWalk()
        super().reject()


    def _updateButtons(self):
        """ Enables/disables buttons depending on if the test is ongaing
        """
        self.walkAllButton.setEnabled(not self._isOngoing)
        self.walkCurrentButton.setEnabled(not self._isOngoing)
        self.abortWalkButton.setEnabled(self._isOngoing)


    def _setProgressFraction(self, fraction: float):
        """ Sets the fraction (percentage / 100)
        """
        self.progressBar.setValue(int(round(fraction * 100)))
        logger.debug("Progress fraction {:8.3f}".format(fraction))
        processEvents()


    @QtSlot(int)
    def onShowAllResultsChanged(self, state: int):
        """ Executed when the 'show all results' check box changes
        """
        logger.info("Setting onShowAllResultsChanged: {}".format(state))
        if state == Qt.Checked:
            self._showAllResults = True
        elif state == Qt.Unchecked:
            self._showAllResults = False
        else:
            raise ValueError("Unexpected checkbox state: {}".format(state))


    def appendText(self, text: str, isError: bool = False):
        """ Appends a text message to the editor.
        """
        if not isError:
            self.editor.appendPlainText(text)
        else:
            self.editor.appendHtml(wrapHtmlColor(text, COLOR_ERROR))


    @QtSlot(bool)
    def setTestResult(self, success: bool):
        """ Appends the currently selected path node to the list of tests.

            This slot will be called whenever the inspector or detail tab (properties, attributes,
            quicklook) updates itself.

            Setting the name and result are separate methods because the inspector and detail tab
            don't know which node is currently selected in the repo tree.
        """
        if not self._isOngoing:
            logger.debug("No test ongoing. Test result discarded.")
            return

        if self._currentTestName is None:
            # When we test also for different inspector or detail panels, the test with the
            # current inspector & panels is ignored because the same test will be repeated later
            # This prevents showing the same test result again but with a different name.
            logger.debug("Ignoring test with current inspector and detail panel")
            return

        # An inspector may be updated twice during a single test. For example, if a node was not
        # yet expanded, expanding will redraw the inspector for that node. In that case this
        # function will be called twice for the current test. We therefore merge these results.
        if self._results:
            prevSuccess, prevName = self._results[-1]
            if self._currentTestName == prevName:
                logger.debug("Ignoring duplicate test result: {}".format(self._currentTestName))
                # It can happen that test results differ. For instance when the inspector fails
                # but the detail panel succeeds.
                self._results[-1] = (success and prevSuccess, self._currentTestName)
                return

        self._results.append((success, self._currentTestName))

        if self._showAllResults or not success:
            line = "{:8s}: {}".format("success" if success else "FAILED", self._currentTestName)
            logger.info("setTestResult: {}".format(line))
            self.appendText(line, isError=not success)


    @QtSlot()
    def abortTestWalk(self):
        """ Sets the flag to abort the test walk
        """
        self._isOngoing = False
        self._updateButtons()
        self.curPathLabel.setText("Test walk aborted!")


    @QtSlot()
    def walkCurrentRepoNode(self, allInspectors: bool=None, allDetailTabs: bool=None):
        """ Will visit all nodes below the currently selected node
        """
        logger.debug(f"walkCurrentRepoNode: {allInspectors} {allDetailTabs}")
        if allInspectors is not None:
            self.allInspectorsCheckBox.setChecked(allInspectors)

        if allDetailTabs is not None:
            self.allDetailTabsCheckBox.setChecked(allDetailTabs)

        curItem, _curIdx = self.repoTreeView.getCurrentItem()
        if curItem is None:
            logger.warning("No node selected for test walk")
        else:
            logger.info("Test walk current item: {}".format(curItem.nodePath))
            self.walkRepoNodes([curItem.nodePath])


    @QtSlot()
    def walkAllRepoNodes(self, allInspectors: bool=None, allDetailTabs: bool=None):
        """ Will visit all nodes in the repo tree.

            See walkRepoNodes docstring for more info
        """
        logger.info("testWalkAllNodes")
        if allInspectors is not None:
            self.allInspectorsCheckBox.setChecked(allInspectors)

        if allDetailTabs is not None:
            self.allDetailTabsCheckBox.setChecked(allDetailTabs)

        repo = self.repoTreeView.model()
        nodePaths = [rti.nodePath for rti in repo.rootItems()]
        logger.debug("All root items: {}".format(nodePaths))
        self.walkRepoNodes(nodePaths)


    def walkRepoNodes(self, nodePaths):
        """ Will recursively walk through a list of repo tree nodes and all their descendants

            Is useful for testing.
        """
        logger.info("-------------- Running Tests ----------------")
        logger.debug("Visiting all nodes below: {}".format(nodePaths))

        self.show()
        self._currentTestName = None
        self._results = []
        self.editor.clear()

        nodesVisited = 0
        logger.debug("Starting test walk")
        self._isOngoing = True
        self._updateButtons()

        # Unselect the current item to force the first node to trigger a new inspector
        originalIndex = self.repoTreeView.currentIndex()
        invalidIndex = self.repoTreeView.model().index(-1, -1)
        assert not invalidIndex.isValid(), "sanity check"
        self.repoTreeView.setCurrentIndex(invalidIndex)

        # Similarly, select the last detail panel to force the first to trigger a new result
        self.repoWidget.tabWidget.setCurrentIndex(self.repoWidget.tabWidget.count()-1)

        try:
            timeAtStart = time.perf_counter()
            check_is_a_sequence(nodePaths) # prevent accidental iteration over strings.

            for numVisited, nodePath in enumerate(nodePaths):
                nodeItem, nodeIndex = self.repoTreeView.model().findItemAndIndex(nodePath)

                assert nodeItem is not None, "Test data not found, rootNode: {}".format(nodePath)
                assert nodeIndex

                progressRange = (numVisited / len(nodePaths), (numVisited+1) / len(nodePaths))
                nodesVisited += self._visitNodes(nodeIndex, progressRange)

            if self._isOngoing:
                self._setProgressFraction(1.0)

            duration = time.perf_counter() - timeAtStart
            self._logTestSummary(duration, nodesVisited)
            self._displayTestSummary(duration, nodesVisited)
        finally:
            logger.debug("Stopping test walk")
            self._isOngoing = False
            self._currentTestName = None
            self._updateButtons()
            if self._isOngoing:
                self.repoTreeView.setCurrentIndex(originalIndex)
            logger.info("-------------- Test walk done ----------------")


    def _visitNodes(self, index: QtCore.QModelIndex, progressRange: Tuple[float, float]) -> int:
        """ Helper function that visits all the nodes recursively.

            Args:
                index: current node index
                progressRange: range that this call will cover in the progress bar.

            Returns:
                The number of nodes that where visited.
        """
        assert index.isValid(), "sanity check"

        if not self._isOngoing:
            return 0  # Test walk aborted.

        repoModel = self.repoTreeView.model()
        item = repoModel.getItem(index)
        logger.info("Visiting: {!r} ({} children)".
                    format(item.nodePath, repoModel.rowCount(index)))

        self.curPathLabel.setText(item.nodePath)

        # Select index
        if item.nodeName.startswith('_'):
            logger.warning("Skipping node during testing: {}".format(item.nodePath))
            return 0
        else:
            logger.debug("Not skipping node during testing: {}".format(item.nodePath))

        if self.allDetailTabsCheckBox.isChecked() or self.allInspectorsCheckBox.isChecked():
            self._currentTestName = None
        else:
            self._currentTestName = "{}".format(item.nodePath)
            processEvents()

        wasOpen = self.repoTreeView.isExpanded(index)
        self.repoTreeView.setCurrentIndex(index)
        self.repoTreeView.expand(index)

        if self.allDetailTabsCheckBox.isChecked():
            # Try properties, attributes and quicklook tabs
            for idx in range(self.repoWidget.tabWidget.count()):
                tabName = self.repoWidget.tabWidget.tabText(idx)
                self._currentTestName = "{:11}: {}".format(tabName, item.nodePath)
                logger.debug("Setting repo detail tab : {}".format(tabName))
                self.repoWidget.tabWidget.setCurrentIndex(idx)
                processEvents()

        if self.allInspectorsCheckBox.isChecked():
            for action in self._mainWindow.inspectorActionGroup.actions():
                assert action.text(), "Action text undefined: {!r}".format(action.text())
                self._currentTestName = "{:11}: {}".format(action.text(), item.nodePath)
                action.trigger()
                processEvents()

        nodesVisited = 1

        prMin, prMax = progressRange
        prLength = prMax - prMin
        self._setProgressFraction(prMin)
        logger.debug("Range {:8.3f}, {:8.3f}: {}".format(prMin, prMax, item.nodePath))

        toVisit = repoModel.rowCount(index)
        for numVisited, rowNr in enumerate(range(toVisit)):
            childIndex = repoModel.index(rowNr, 0, parentIndex=index)
            subRange = (prMin + numVisited / toVisit * prLength,
                        prMin + (numVisited+1) / toVisit * prLength)
            nodesVisited += self._visitNodes(childIndex, subRange)

        if self._isOngoing and not wasOpen:
            self.repoTreeView.closeItem(index)

        return nodesVisited


    def _displayTestSummary(self, duration: float, nodesVisited: int):
        """ Displays a test summary in the dialog
        """
        self.appendText('-' * 80)
        if self._isOngoing:
            self.appendText("Test finished.")
        else:
            self.appendText("Test ABORTED", isError=True)


    def _logTestSummary(self, duration: float, nodesVisited: int):
        """ Logs a summary of the test results.
        """
        logger.info("Visited {} nodes in {:.1f} seconds ({:.1f} nodes/second)."
                    .format(nodesVisited, duration, nodesVisited/duration))

        failedTests = [(success, name) for success, name in self._results if not success]
        logger.info("Number of failed tests during test walk: {}".format(len(failedTests)))
        for testName in failedTests:
            logger.info("    {}".format(testName))

        if not self._isOngoing:
            logger.info("")
            logger.info("NOTE: the test walk was aborted!")
        else:
            # Check that the number of test results is as expected
            allInspect = self.allInspectorsCheckBox.isChecked()
            allDetail = self.allDetailTabsCheckBox.isChecked()
            if allInspect or allDetail:
                numInspectors = len(self._mainWindow.inspectorActionGroup.actions())
                numDetailPanels = self.repoWidget.tabWidget.count()
                factor = numInspectors * int(allInspect) + numDetailPanels * int(allDetail)
            else:
                factor = 1

            expectedNumResuls = nodesVisited * factor
            if len(self._results) != expectedNumResuls:
                msg = "Actual nr of results ({}) != expected nr of results: {}"\
                    .format(len(self._results), expectedNumResuls)
                logger.warning(msg)

                # No assert, as this can happen when there are two nodes with the same name, which
                # is common in NetCDF files that follow the CF conventions.
                #assert False, msg
