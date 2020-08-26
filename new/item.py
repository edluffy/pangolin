from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QStandardItem
from PyQt5.QtWidgets import (QGraphicsItem, QGraphicsItemGroup,
                             QGraphicsPathItem, QStyle, QWidget)

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
            self.gfx = QGraphicsPathItem()
        elif self.type == "Path":
            self.gfx = PangoPathGraphic()
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

class PangoPathGraphic(QGraphicsPathItem):
    def __init__ (self, parent=None):
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setOpacity(0.8)
        self.set_pen(width=10)

    def set_pen(self, color=None, width=None):
        pen = self.pen()
        
        if color is not None:
            pen.setColor(color)
        if width is not None:
            pen.setWidth(width)

        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)

    def paint(self, painter, option, widget):
        if option.state & QStyle.State_Selected:
            self.setOpacity(1)
        elif option.state & QStyle.State_MouseOver:
            self.setOpacity(0.5)
        else:
            self.setOpacity(0.8)

        option.state &= ~QStyle.State_Selected
        option.state &= ~QStyle.State_MouseOver
        super().paint(painter, option, widget)

