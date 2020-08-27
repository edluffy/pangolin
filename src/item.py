from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QStandardItem
from PyQt5.QtWidgets import (QGraphicsEllipseItem, QGraphicsItem,
                             QGraphicsItemGroup, QGraphicsPathItem,
                             QGraphicsPolygonItem, QStyle, QWidget)

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
        elif self.type == "Poly":
            self.gfx = PangoPolyGraphic()
        elif self.type == "Dot":
            self.gfx = PangoDotGraphic()
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

class PangoGraphicMixin(object):
    def paint(self, painter, option, widget):
        if option.state & QStyle.State_Selected:
            self.setOpacity(1)
        elif option.state & QStyle.State_MouseOver:
            self.setOpacity(0.2)
        else:
            self.setOpacity(0.5)
        option.state &= ~QStyle.State_Selected
        option.state &= ~QStyle.State_MouseOver
        super().paint(painter, option, widget)

    def set_pen(self, color=None, width=None):
        pen = self.pen()
        if color is not None:
            pen.setColor(color)
        if width is not None:
            pen.setWidth(width)
        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)

    def set_brush(self, color):
        brush = self.brush()
        brush = QtGui.QBrush()
        brush.setColor(QColor(color))
        brush.setStyle(Qt.SolidPattern)
        self.setBrush(brush)

class PangoPathGraphic(PangoGraphicMixin, QGraphicsPathItem):
    def __init__(self, parent=None):
        super().__init__()
        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsMovable)

        self.setAcceptHoverEvents(True)
        self.set_pen(width=10)


class PangoPolyGraphic(PangoGraphicMixin, QGraphicsPolygonItem):
    def __init__ (self, parent=None):
        super().__init__()
        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsMovable)

        self.setAcceptHoverEvents(True)
        self.set_pen(width=10)

class PangoDotGraphic(PangoGraphicMixin, QGraphicsEllipseItem):
    def __init__(self, parent=None):
        super().__init__()
        self.setFlags(QGraphicsItem.ItemIsSelectable
                      | QGraphicsItem.ItemIsMovable
                      | QGraphicsItem.ItemIgnoresParentOpacity
                      | QGraphicsItem.ItemSendsGeometryChanges)

        self.setAcceptHoverEvents(True)
        self.setOpacity(0.5)
        self.set_pen(width=10)

        self.setZValue(1)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            print("pos: ", value)
        return value
