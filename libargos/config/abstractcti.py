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

""" Configuration TreeItem (CTI) classes
    Tree items for use in the ConfigTreeModel
"""
import logging, os
from json import JSONEncoder, JSONDecoder, dumps

from libargos.info import DEBUGGING, icons_directory
from libargos.qt import Qt, QtCore, QtGui, QtSlot
from libargos.qt.treeitems import BaseTreeItem
from libargos.utils.cls import get_full_class_name, import_symbol
from libargos.utils.misc import NOT_SPECIFIED


logger = logging.getLogger(__name__)


class InvalidInputError(Exception):
    """ Exception raised when the input is invalid after editing
    """
    pass


class AbstractCtiEditor(QtGui.QWidget):
    """ An editor for use in the ConfigTreeView (CTI).
    
        It is a horizontal collection of child widgets, the last of which is a reset button.
        The reset button will reset the config data to its default.
        
    """
    def __init__(self, cti, delegate, subEditors, parent=None):
        """ Wraps the child widgets in a horizontal layout and appends a reset button.
            
            Maintains a reference to the ConfigTreeItem (cti) and to delegate, this last reference
            is so that we can command the delegate to commit and close the editor.
            
            The subEditors must be a list of QWidgets. The first sub editor is considered the 
            main editor. This editor will receive the focus. Note that the sub editors do not yet
            have to be initialized with editor data since setData will be called by the delegate 
            after construction. There it can be taken care of.
        """
        super(AbstractCtiEditor, self).__init__(parent=parent)

        assert len(subEditors) >= 1, "You should specify at least one childWidget"

        self.delegate = delegate
        self.cti = cti
        
        hBoxLayout = QtGui.QHBoxLayout()
        hBoxLayout.setContentsMargins(0, 0, 0, 0)
        hBoxLayout.setSpacing(0)
        self.setLayout(hBoxLayout)

        self.subEditors = subEditors
        for subEditor in subEditors:
            hBoxLayout.addWidget(subEditor)

        self.resetButton = QtGui.QToolButton()
        self.resetButton.setText("Reset")
        self.resetButton.setToolTip("Reset to default value.")
        self.resetButton.setIcon(QtGui.QIcon(os.path.join(icons_directory(), 'err.warning.svg')))
        self.resetButton.setFocusPolicy(Qt.NoFocus)
        self.resetButton.clicked.connect(self.resetEditorValue)
        hBoxLayout.addWidget(self.resetButton, alignment=Qt.AlignRight)
        
        # From the QAbstractItemDelegate.createEditor docs: The returned editor widget should have 
        # Qt.StrongFocus; otherwise, QMouseEvents received by the widget will propagate to the view. 
        # The view's background will shine through unless the editor paints its own background 
        # (e.g., with setAutoFillBackground()).
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(self.mainEditor)
        self.mainEditor.setFocusPolicy(Qt.StrongFocus)
        
        self.mainEditor.installEventFilter(self)
        

    def eventFilter(self, watchedObject, event):
        """ Calls commitAndClose when the tab and back-tab are pressed.
            This is necessary because, normally the event filter of QStyledItemDelegate does this
            for us. However, that event filter works on this object, not on the main editor.
        """
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if key in (Qt.Key_Tab, Qt.Key_Backtab):
                self.commitAndClose()
                return True
            else:
                return False

        return super(AbstractCtiEditor, self).eventFilter(watchedObject, event) 
            

    def finalize(self):
        """ Called at clean up. Can be used to disconnect signals.
        """
        logger.debug("BaseCtiEditor.finalize")
        self.mainEditor.removeEventFilter(self)
        self.resetButton.clicked.disconnect(self.resetEditorValue)
        self.cti = None # just to make sure it's not used again.
        self.delegate = None

        
    def setData(self, value):
        """ Provides the main editor widget with a data to manipulate.
            Value originates from the ConfigTreeModel.data(role=QEditRole).
        """
        raise NotImplementedError()
        
        
    def getData(self):
        """ Gets data from the editor widget.
            Should return a value that can be set into the ConfigTreeModel with the QEditRole.
        """
        raise NotImplementedError()
    
        
    @property
    def mainEditor(self):
        """ Returns the first child widget 
        """
        return self.subEditors[0]
    
    
    @QtSlot()
    def commitAndClose(self):
        """ Commits the data of the main editor and instructs the delegate to close this ctiEditor.
        
            The delegate will emit the closeEditor signal which is connected to the closeEditor
            method of the ConfigTreeView class. This, in turn will, call the finalize method of
            this object so that signals can be disconnected and resources can be freed. This is
            complicated but I don't see a simpler solution.
        """
        self.delegate.commitData.emit(self)
        self.delegate.closeEditor.emit(self, QtGui.QAbstractItemDelegate.NoHint)   # CLOSES SELF!
        

    @QtSlot(bool)
    def resetEditorValue(self, checked=False):
        """ Resets the main editor to the default value of the config tree item
        """
        logger.debug("resetEditorValue: {}".format(checked))
        self.setData(self.cti.defaultData)
        self.commitAndClose()
    
    
    def paintEvent(self, event):
        """ Reimplementation of paintEvent to allow for style sheets
            See: http://qt-project.org/wiki/How_to_Change_the_Background_Color_of_QWidget
        """
        opt = QtGui.QStyleOption()
        opt.initFrom(self)
        painter = QtGui.QPainter(self)
        self.style().drawPrimitive(QtGui.QStyle.PE_Widget, opt, painter, self)
        painter.end()
        
        