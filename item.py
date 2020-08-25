
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QStandardItem
from PyQt5.QtWidgets import QGraphicsItemGroup, QGraphicsPathItem

from widgets.utils import PangoDockWidget, PangoPalette


class PangoStandardItem(QStandardItem):
    def __init__(self, type=None, parent=QStandardItem()):
        super().__init__()
        self.type = type

        parent.appendRow(self)
        row = self.index().row()

        name = self.type + " " + str(row)
        if parent.index().row() == -1:
            color = QtGui.QColor(PangoPalette[(row+1)%len(PangoPalette)])
            visible = Qt.Checked
        else:
            color = parent.data(Qt.DecorationRole)
            visible = parent.data(Qt.CheckStateRole)

        self.setData(name, Qt.DisplayRole)
        self.setData(color, Qt.DecorationRole)
        self.setData(visible, Qt.CheckStateRole)

        self.setCheckable(True)

    def map_index(self):
        return QtCore.QPersistentModelIndex(self.index())

class PangoGraphicsPathItem(QGraphicsPathItem):
    def __init__(self, parent=QGraphicsItemGroup()):
        super().__init__()

        pen = QPen()
        pen.setWidth(10)
        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)

        parent.addToGroup(self)

