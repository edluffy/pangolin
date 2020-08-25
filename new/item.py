from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QColor
from PyQt5.QtWidgets import QWidget, QGraphicsItem, QGraphicsPathItem, QGraphicsItemGroup

PangoPalette = [QColor('#e6194b'), QColor('#3cb44b'), QColor('#ffe119'),
                QColor('#4363d8'), QColor('#f58231'), QColor('#911eb4'),
                QColor('#46f0f0'), QColor('#f032e6'), QColor('#bcf60c'),
                QColor('#fabebe'), QColor('#008080'), QColor('#e6beff'),
                QColor('#9a6324'), QColor('#fffac8'), QColor('#800000'),
                QColor('#aaffc3'), QColor('#808000'), QColor('#ffd8b1'),
                QColor('#000075'), QColor('#808080')]

class PangoHybridItem(QStandardItem):
    def __init__ (self, type, parent=None):
        super().__init__()
        self.type = type

        if self.type == "Label":
            self.gfx = QGraphicsItemGroup()
        elif self.type == "Path":
            self.gfx = PangoPathItem()
        else:
            self.gfx = QGraphicsItem()
        self.setData(self.gfx, Qt.UserRole)

        parent.appendRow(self)
        self.gfx.setData(0, QtCore.QPersistentModelIndex(self.index()))

        parent_gfx = parent.data(Qt.UserRole)
        if parent_gfx is not None:
            self.gfx.setParentItem(parent_gfx)
            color = parent.data(Qt.DecorationRole)
        else:
            color = PangoPalette[self.row() % len(PangoPalette)]

        # Item specific defaults
        self.setData(self.type, Qt.DisplayRole)
        self.setData(color, Qt.DecorationRole)
        self.setData(Qt.Checked, Qt.CheckStateRole)
        self.setCheckable(True)

        self.gfx.setFlag(QGraphicsItem.ItemIsSelectable)

class PangoPathItem(QGraphicsPathItem):
    def __init__ (self, parent=None):
        super().__init__()

        pen = self.pen()
        pen.setWidth(10)
        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)


    def mouseMoveEvent(self, event):
        pen = self.pen()
        color = pen.color()
        color.setAlphaF(0.5)
        pen.setColor(color)
        self.setPen(pen)



