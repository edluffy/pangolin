from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import (QColor, QPainter, QPainterPath, QPolygonF,
                         QStandardItem)
from PyQt5.QtWidgets import (QGraphicsEllipseItem, QGraphicsItem,
                             QGraphicsItemGroup, QGraphicsPathItem,
                             QGraphicsPolygonItem, QGraphicsRectItem, QStyle,
                             QWidget)

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
        elif self.type == "Filled Path":
            self.gfx = PangoFilledPathGraphic()
        elif self.type == "Rect":
            self.gfx = PangoRectGraphic()
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
    def set_opacity(self, painter, option):
        #painter.setCompositionMode(QPainter.CompositionMode_Source)
        if option.state & QStyle.State_Selected:
            self.setOpacity(1)
        elif option.state & QStyle.State_MouseOver:
            self.setOpacity(0.8)
        else:
            self.setOpacity(0.5)
        option.state &= ~QStyle.State_Selected
        option.state &= ~QStyle.State_MouseOver

    def p_index(self):
        return self.data(0)

    def change_pen(self, color=None, width=None, style=None):
        if hasattr(self, "pen"):
            pen = self.pen()
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            if color is not None:
                pen.setColor(color)
            if width is not None:
                pen.setWidth(width)
            if style is not None:
                pen.setStyle(style)
            self.setPen(pen)

    def change_brush(self, color=None, style=None):
        if hasattr(self, "brush"):
            brush = self.brush()
            if color is not None:
                brush.setColor(color)
            if style is not None:
                brush.setStyle(style)
            self.setBrush(brush)

class PangoPathGraphic(PangoGraphicMixin, QGraphicsPathItem):
    def __init__(self, parent=None):
        super().__init__()
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsMovable)

    def set_decoration(self, color=None, width=None):
        self.change_pen(color, width)

    def paint(self, painter, option, widget):
        self.set_opacity(painter, option)
        super().paint(painter, option, widget)

class PangoFilledPathGraphic(PangoPathGraphic):
    def __init__(self, parent=None):
        super().__init__()

    def set_decoration(self, color=None, width=None):
        super().set_decoration(color, width)
        self.change_brush(color, Qt.SolidPattern)

class PangoRectGraphic(PangoGraphicMixin, QGraphicsRectItem):
    def __init__(self, parent=None):
        super().__init__()
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsMovable)

    def set_decoration(self, color=None, width=None, style=None):
        self.change_pen(color, 10)
        self.change_brush(color, style)

    def paint(self, painter, option, widget):
        self.set_opacity(painter, option)
        super().paint(painter, option, widget)

class PangoPolyGraphic(PangoGraphicMixin, QGraphicsPolygonItem):
    def __init__ (self, parent=None):
        super().__init__()
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsMovable)

        self.closed = False

    def close_poly(self, state):
        self.closed = state
        self.update()

    def set_decoration(self, color=None, width=None, style=None):
        self.change_pen(color, 10)
        self.change_brush(color, style)

    def paint(self, painter, option, widget):
        self.set_opacity(painter, option)

        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        poly = self.polygon()

        if self.closed:
            self.change_brush(style=Qt.SolidPattern)
            painter.drawPolygon(poly)
        else:
            path = QPainterPath()
            path.moveTo(poly.at(0))
            for n in range(1, len(poly)):
                path.lineTo(poly.at(n))
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

    def move_dot(self, value):
        parent = self.p_index().parent().data(Qt.UserRole)
        parent_item = self.p_index().model().itemFromIndex(
            QtCore.QModelIndex(self.p_index().parent()))

        if parent_item.type == "Rect":
            rect = parent.rect().toRect()
            if self.origin == None:
                if self.p_index().row() == 0:
                    self.origin = rect.topLeft()
                else:
                    self.origin = rect.bottomRight()
            else:
                if self.p_index().row() == 0:
                    rect.setTopLeft((self.origin+value).toPoint())
                else:
                    rect.setBottomRight((self.origin+value).toPoint())

            parent.setRect(QRectF(rect))

        elif parent_item.type == "Poly":
            poly = parent.polygon().toPolygon()
            if self.origin == None:
                self.origin = poly.point(self.p_index().row())
            poly.setPoint(self.p_index().row(), (self.origin+value).toPoint())
            parent.setPolygon(QPolygonF(poly))

    def set_decoration(self, color=None, width=None):
        self.change_pen(color, 10)
        self.change_brush(QColor("black"))

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.move_dot(value)
        return value

    def paint(self, painter, option, widget):
        self.set_opacity(painter, option)
        super().paint(painter, option, widget)
