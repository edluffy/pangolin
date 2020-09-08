from PyQt5.QtCore import QLineF, QPointF, Qt, QRectF, QPersistentModelIndex, QModelIndex
from PyQt5.QtGui import QBrush, QColor, QIcon, QPainter, QPainterPath, QPainterPathStroker, QPen, QPolygonF, QStandardItem
from PyQt5.QtWidgets import (QAbstractGraphicsShapeItem, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem,
                             QGraphicsPolygonItem, QGraphicsRectItem, QStyle)

from utils import PangoShapeType, pango_get_icon, pango_get_palette

class PangoHybridItem(QStandardItem):
    def __init__ (self, type):
        super().__init__()
        self.set_type(type)
        self.setCheckable(True)

        self._color = QColor()
        self._icon = ""

    def key(self):
        return QPersistentModelIndex(self.index())

    def type(self):
        return self.data(Qt.UserRole)

    def set_type(self, shape):
        self.setData(shape, Qt.UserRole)
    
    def name(self):
        return self.data(Qt.DisplayRole)
    
    def set_name(self, name):
        self.setData(name, Qt.DisplayRole)

    def decoration(self):
        return (self._icon, self._color)

    def set_decoration(self, decoration=None):
        if decoration == self.decoration():
            return
        if decoration is not None:
            self._icon, self._color = decoration
            self.setData(pango_get_icon(self._icon, self._color), Qt.DecorationRole)
        else:
            if self.parent() is None:
                self._color = pango_get_palette(self.row())
            else:
                self._color = self.parent().color()

            if self.type() == PangoShapeType.Path:
                self._icon = "path"
            elif self.type() == PangoShapeType.Rect:
                self._icon = "rect"
            elif self.type() == PangoShapeType.Poly:
                self._icon = "poly"
            else:
                self._icon = "label"

            self.setData(pango_get_icon(self._icon, self._color), Qt.DecorationRole)

    def visible(self):
        return self.data(Qt.CheckStateRole) == Qt.Checked

    def set_visible(self, state):
        self.setData(Qt.Checked if state else Qt.Unchecked, Qt.CheckStateRole)

class PangoGraphic(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

        self._icon = ""
        self._pen = QPen()
        self._pen.setCapStyle(Qt.RoundCap)
        self._pen.setJoinStyle(Qt.RoundJoin)
        self._brush = QBrush()
 
    def name(self):
        return self.toolTip()
    
    def set_name(self, name):
        self.setToolTip(name)

    def decoration(self):
        return (self._icon, self._pen.color())
    
    def set_decoration(self, decoration=None):
        if decoration == self.decoration():
            return
        if decoration is not None:
            icon, color = decoration
            self._pen.setColor(color)
            self._icon = icon
        else:
            if self.parentItem() is None:
                self._pen.setColor(pango_get_palette(len(self.scene().items())))
            else:
                self._pen.setColor(self.parentItem().decoration()[1])

            if self.type() == PangoShapeType.Path:
                self._icon = "path"
            elif self.type() == PangoShapeType.Rect:
                self._icon = "rect"
            elif self.type() == PangoShapeType.Poly:
                self._icon = "poly"
            else:
                self._icon = "label"

        # Hijack 'ItemTransformHasChanged' since not being used anyway
        if self.scene() is not None:
            self.scene().gfx_changed.emit(self, QGraphicsItem.ItemTransformHasChanged)
        self.update()

    def visible(self):
        return self.isVisible()

    def set_visible(self, state):
        self.setVisible(state)

    def itemChange(self, change, value):
        if self.scene() is not None:
            self.scene().gfx_changed.emit(self, change)
        return value

    def paint(self, painter, option, widget):
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.setPen(self._pen)
        painter.setBrush(self._brush)

        if option.state & QStyle.State_Selected:
            painter.setOpacity(0.7)
        else:
            painter.setOpacity(0.5)

    def boundingRect(self):
        return QRectF()

    def type(self):
        return PangoShapeType.Default

class PangoPathGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._points = []

    def set_width(self, width=None):
        if width is not None:
            self._pen.setWidth(width)

    def add_point(self, pnt, action):
        self._points.append((pnt, action))

    def pop_point(self):
        return self._points.pop()
    
    def path(self):
        if len(self._points) > 1:
            path = QPainterPath(self._points[0][0])
            for point, action in self._points[1:]:
                if action == 0:
                    path.lineTo(point)
                else:
                    path.moveTo(point)
            return path
        else:
            return QPainterPath()

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        painter.drawPath(self.path())

    def boundingRect(self):
        return self.shape().controlPointRect()

    def shape(self):
        st = QPainterPathStroker(self._pen)
        return st.createStroke(self.path())

    def type(self):
        return PangoShapeType.Path


class PangoPolyGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._polygon = QPolygonF()
        self._closed = False

        self.w = 10
        self._pen.setWidth(self.w)
        self._brush.setStyle(Qt.SolidPattern)

    def add_point(self, pnt):
        if len(self._polygon) > 1 and (QLineF(self._polygon.first(), pnt).length() <= self.w):
            self._closed = True
        else:
            self._polygon += pnt

    def rem_point(self):
        if self._polygon.count() > 1:
            self._polygon.remove(self._polygon.count()-1)
            self._closed = False

    def points(self):
        pnts = []
        for n in range(0, self._polygon.count()):
            pnts.append(self._polygon.value(n))
        return pnts

    def closed(self):
        return self._closed
    
    def set_decoration(self, decoration=None):
        super().set_decoration(decoration)
        self._brush.setColor(self._pen.color())

    def hoverMoveEvent(self, event):
        pass

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self._closed:
            painter.drawPolygon(self._polygon)
        else:
            for n in range(0, len(self._polygon)-1):
                painter.drawLine(self._polygon.value(n),
                                 self._polygon.value(n+1))

        if option.state & QStyle.State_MouseOver:
            painter.setOpacity(1)
            for n in range(0, len(self._polygon)):
                painter.drawRect(self._polygon.value(n).x()-5,
                                 self._polygon.value(n).y()-5, 10, 10)

    def boundingRect(self):
        return self.shape().controlPointRect().adjusted(-self.w, -self.w, self.w, self.w)

    def shape(self):
        path = QPainterPath()
        path.addPolygon(self._polygon)

        st = QPainterPathStroker()
        st.setWidth(self._pen.width())
        st.setJoinStyle(self._pen.joinStyle())
        outline = st.createStroke(path)

        path.addPath(outline)
        return path

    def type(self):
        return PangoShapeType.Poly


class PangoRectGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)

