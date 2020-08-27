from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QStandardItem, QPolygonF, QPainter, QPainterPath
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
            self.gfx = PangoPathGraphic()
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
    def hover_override(self, op_state):
        if op_state & QStyle.State_Selected:
            self.setOpacity(1)
        elif op_state & QStyle.State_MouseOver:
            self.setOpacity(0.8)
        else:
            self.setOpacity(0.5)
        op_state &= ~QStyle.State_Selected
        op_state &= ~QStyle.State_MouseOver

    def p_index(self):
        return self.data(0)

    def set_pen(self, color=None, width=None):
        if hasattr(self, "pen"):
            pen = self.pen()
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            if color is not None:
                pen.setColor(color)
            if width is not None:
                pen.setWidth(width)
            self.setPen(pen)

    def set_brush(self, color=None):
        if hasattr(self, "brush"):
            brush = self.brush()
            brush.setStyle(Qt.SolidPattern)
            if color is not None:
                brush.setColor(color)
            self.setBrush(brush)

class PangoPathGraphic(PangoGraphicMixin, QGraphicsPathItem):
    def __init__(self, parent=None):
        super().__init__()
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsMovable)

    def set_decoration(self, color=None, width=None):
        pen = self.pen()
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setWidth(10)
        if color is not None:
            pen.setColor(color)
        if width is not None:
            pen.setWidth(width)
        self.setPen(pen)

    def paint(self, painter, option, widget):
        painter.setCompositionMode(QPainter.CompositionMode_Difference)
        self.hover_override(option.state)
        super().paint(painter, option, widget)


class PangoPolyGraphic(PangoGraphicMixin, QGraphicsPolygonItem):
    def __init__ (self, parent=None):
        super().__init__()
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsMovable)

    def set_decoration(self, color=None, width=None):
        self.set_pen(color, 5)

    def paint(self, painter, option, widget):
        self.hover_override(option.state)
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        
        path = QPainterPath()
        path.moveTo(self.polygon().at(0))

        for n in range(1, len(self.polygon())):
            path.lineTo(self.polygon().at(n))
            print(self.polygon().at(n))
        print("----------------------")

        painter.drawPath(path)

class PangoDotGraphic(PangoGraphicMixin, QGraphicsEllipseItem):
    def __init__(self, parent=None):
        super().__init__()
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.ItemIsSelectable
                      | QGraphicsItem.ItemIsMovable
                      | QGraphicsItem.ItemIgnoresParentOpacity
                      | QGraphicsItem.ItemSendsGeometryChanges)

        self.origin = None

    def set_decoration(self, color=None, width=None):
        self.set_pen(color, 5)
        self.set_brush(QColor("black"))

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            parent = self.p_index().parent().data(Qt.UserRole)
            poly = parent.polygon().toPolygon()

            if self.origin == None:
                self.origin = poly.point(self.p_index().row())
            poly.setPoint(self.p_index().row(), (self.origin+value).toPoint())

            parent.setPolygon(QPolygonF(poly))
        return value

    def paint(self, painter, option, widget):
        self.hover_override(option.state)
        super().paint(painter, option, widget)

