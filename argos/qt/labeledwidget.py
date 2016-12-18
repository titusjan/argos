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

""" Defines ToggleColumnMixIn class
"""
from __future__ import print_function

import logging

from argos.qt import QtCore, QtWidgets, Qt

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901


class LabeledWidget(QtWidgets.QWidget):
    """ A places a label and a widget next to each other.

        The layout will be created. It can be accessed as self.layout
        The label is passed as parameter and can be accessed as self.label
        The widget is passed as parameter and is available as self.widget
    """

    def __init__(self, label, widget,
                 layoutSpacing = None,
                 layoutContentsMargins = (0, 0, 0, 0),
                 labelStretch=0, spacerStretch=0, widgetStretch=1,
                 parent=None):
        """ Constructor.

            :param widget: the 'wrapped' widget, which will be displayed on the right
            :param labelText: text given to the label
            :param parent: parent wigdet
        """
        super(LabeledWidget, self).__init__(parent=parent)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(*layoutContentsMargins)
        if layoutSpacing is not None:
            self.layout.setSpacing(layoutSpacing)
        self.label = label
        self.widget = widget

        self.layout.addWidget(self.label, stretch=labelStretch)
        if spacerStretch:
            self.layout.addStretch(stretch=spacerStretch)
        self.layout.addWidget(self.widget, stretch=widgetStretch)



def labelTextWidth(label):
    """ Returns the width of label text of the label in pixels.

        IMPORTANT: does not work when the labels are styled using style sheets.

        Unfortunately it is possible to retrieve the settings (e.g. padding) that were set by the
        style sheet without parsing the style sheet as text.
    """
    # The Qt source shows that fontMetrics().size calls fontMetrics().boundingRect with
    # the TextLongestVariant included in the flags. TextLongestVariant is an internal flag
    # which is used to force selecting the longest string in a multi-length string.
    # See: http://stackoverflow.com/a/8638114/625350
    fontMetrics = label.fontMetrics()
    #contentsWidth = label.fontMetrics().boundingRect(label.text()).width()
    contentsWidth = fontMetrics.size(label.alignment(), label.text()).width()

    # If indent is negative, or if no indent has been set, the label computes the effective indent
    # as follows: If frameWidth() is 0, the effective indent becomes 0. If frameWidth() is greater
    # than 0, the effective indent becomes half the width of the "x" character of the widget's
    # current font().
    # See http://doc.qt.io/qt-4.8/qlabel.html#indent-prop
    if label.indent() < 0 and label.frameWidth(): # no indent, but we do have a frame
        indent = fontMetrics.width('x') / 2 - label.margin()
        indent *= 2 # the indent seems to be added to the other side as well
    else:
        indent = label.indent()

    result = contentsWidth + indent + 2 * label.frameWidth() + 2 * label.margin()

    if 1:
        #print ("contentsMargins: {}".format(label.getContentsMargins()))
        #print ("contentsRect: {}".format(label.contentsRect()))
        #print ("frameRect: {}".format(label.frameRect()))
        print ("contentsWidth: {}".format(contentsWidth))
        print ("lineWidth: {}".format(label.lineWidth()))
        print ("midLineWidth: {}".format(label.midLineWidth()))
        print ("frameWidth: {}".format(label.frameWidth()))
        print ("margin: {}".format(label.margin()))
        print ("indent: {}".format(label.indent()))
        print ("actual indent: {}".format(indent))
        print ("RESULT: {}".format(result))
        print ()
    return result


def labelsMaxTextWidth(labels):
    """ Returns the maximum width of the labels.
        IMPORTANT: does not work when the labels are styled using style sheets.
    """
    return max([labelTextWidth(label) for label in labels])


def harmonizeLabelsTextWidth(labels, width=None):
    """ Sets the the maximum width of the labels
        If width is None, the maximum width is calculated using labelsMaxTextWidth()
    """
    if width is None:
        width = labelsMaxTextWidth(labels)

    for label in labels:
        #label.setFixedWidth(width)
        label.setMinimumWidth(width)


if __name__ == "__main__":

    def _setLabelProps(label):
        #label.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Raised)
        label.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Plain)
        label.setLineWidth(1)

        #label.setMidLineWidth(10)
        #label.setMargin(25)
        #label.setIndent(4)
        #self.label.setAlignment(QtCore.Qt.AlignCenter)
        #self.label.setMaximumWidth(labelMinimumWidth)


    class MyTableView(QtWidgets.QTableView):

        def __init__(self):
            super(MyTableView, self).__init__()

            model = QtGui.QStandardItemModel(3, 2)
            self.setModel(model)
            self.horizontalHeader().resizeSection(0, 200)
            self.horizontalHeader().resizeSection(1, 300)




    def main():
        import sys

        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(window)

        if 0:
            if 1:
                window.setStyleSheet("""
                    QLabel {
                        background-color: #FF9900;
                    }
                """)
            else:
                window.setStyleSheet("""
                    QLabel {
                        margin: 5px;
                        border: 0px solid blue;
                        background-color: #FF9900;
                        padding: 0px;
                    }
                """)

        label0 = QtWidgets.QLabel('my great line edit')
        label1 = QtWidgets.QLabel('edit')
        label2 = QtWidgets.QLabel('combo')

        all_labels = [label0, label1, label2]
        for lbl in all_labels:
            _setLabelProps(lbl)
        harmonizeLabelsTextWidth(all_labels)

        maxWidth = labelsMaxTextWidth([label0, label1, label2])
        print("\mmaxWidth: {}".format(maxWidth))

        tableView =QtWidgets.QTableView()
        layout.addWidget(tableView)
        model = QtGui.QStandardItemModel(3, 2)
        tableView.setModel(model)
        tableView.horizontalHeader().resizeSection(0, 200)
        tableView.horizontalHeader().resizeSection(1, 300)
        layoutSpacing = 0

        editor0 = QtWidgets.QSpinBox()
        editor0.setValue(5)
        editor0.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        lw0 = LabeledWidget(label0, editor0, layoutSpacing=layoutSpacing)
        model.setData(model.index(0, 0), "A small")
        tableView.setIndexWidget(model.index(0, 1), lw0)

        editor1 = QtWidgets.QSpinBox()
        editor1.setValue(7)
        editor1.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        lw1 = LabeledWidget(label1, editor1, layoutSpacing=layoutSpacing)
        model.setData(model.index(1, 0), "A SMALL seasoned curly")
        tableView.setIndexWidget(model.index(1, 1), lw1)

        comboBox = QtWidgets.QComboBox()
        comboBox.addItems(["Half diet coke", "Half regular coke", "Junior western bacon cheese"])
        lw2 = LabeledWidget(label2, comboBox, layoutSpacing=layoutSpacing)
        model.setData(model.index(2, 0), "What else?")
        tableView.setIndexWidget(model.index(2, 1), lw2)

        window.resize(550, 400)
        window.show()
        window.raise_()
        sys.exit(app.exec_())

    #######
    main()



