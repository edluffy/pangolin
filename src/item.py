from PyQt5.QtCore import QLineF, QPoint, QPointF, Qt, QRectF, QPersistentModelIndex, QModelIndex
from PyQt5.QtGui import QBrush, QColor, QIcon, QPainter, QPainterPath, QPainterPathStroker, QPen, QPolygon, QPolygonF, QStandardItem
from PyQt5.QtWidgets import (QAbstractGraphicsShapeItem, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem,
                             QGraphicsPolygonItem, QGraphicsRectItem, QStyle)

from utils import PangoShapeType, pango_get_icon, pango_get_palette

class PangoItem(QStandardItem):
    def __init__ (self):
        super().__init__()
        self.setCheckable(True)
        self.setEditable(False)

        self._color = None
        self._icon = None

    def key(self):
        return QPersistentModelIndex(self.index())

    def setattrs(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    @property
    def fpath(self):
        return self.data(Qt.UserRole)
    
    @fpath.setter
    def fpath(self, fpath):
        self.setData(fpath, Qt.UserRole)

    @property
    def name(self):
        return self.data(Qt.DisplayRole)
    
    @name.setter
    def name(self, name):
        self.setData(name, Qt.DisplayRole)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        if self._color != color:
            self._color = color
            self.decorate()

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, icon):
        if self._icon != icon:
            self._icon = icon
            self.decorate()

    @property
    def visible(self):
        return self.data(Qt.CheckStateRole) == Qt.Checked

    @visible.setter
    def visible(self, state):
        self.setData(Qt.Checked if state else Qt.Unchecked, Qt.CheckStateRole)

    def decorate(self):
        if self._color is None:
            self._color = pango_get_palette(self.row())
        self.setData(pango_get_icon(self._icon, self._color), Qt.DecorationRole)

class PangoLabelItem(PangoItem):
    def __init__(self):
        super().__init__()
        self._icon = "label"

class PangoPathItem(PangoItem):
    def __init__(self):
        super().__init__()
        self._icon = "path"

class PangoPolyItem(PangoItem):
    def __init__(self):
        super().__init__()
        self._icon = "poly"

class PangoRectItem(PangoItem):
    def __init__(self):
        super().__init__()
        self._icon = "rect"

class PangoGraphic(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

        self._fpath = None
        self._icon = ""
        self._pen = QPen()
        self._pen.setCapStyle(Qt.RoundCap)
        self._pen.setJoinStyle(Qt.RoundJoin)
        self._brush = QBrush()
 
    def setattrs(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    @property
    def fpath(self):
        return self._fpath
    
    @fpath.setter
    def fpath(self, fpath):
        self._fpath = fpath
        # Hijack 'ItemMatrixChanged' since not being used anyway
        if self.scene() is not None:
            self.scene().gfx_changed.emit(self, QGraphicsItem.ItemMatrixChange)

    @property
    def name(self):
        return self.toolTip()
    
    @name.setter
    def name(self, name):
        self.setToolTip(name)

    @property
    def color(self):
        return self._pen.color()

    @color.setter
    def color(self, color):
        if self._pen.color() != color:
            self._pen.setColor(color)
            self._brush.setColor(color)
            if self.scene() is not None:
                # Hijack 'ItemTransformHasChanged' since not being used anyway
                self.scene().gfx_changed.emit(self, QGraphicsItem.ItemTransformHasChanged)

    @property
    def icon(self):
        return self._icon
    
    @icon.setter
    def icon(self, icon):
        if self._icon != icon:
            self._icon = icon
            if self.scene() is not None:
                # Hijack 'ItemTransformHasChanged' since not being used anyway
                self.scene().gfx_changed.emit(self, QGraphicsItem.ItemTransformHasChanged)

    @property
    def visible(self):
        return self.isVisible()

    @visible.setter
    def visible(self, visible):
        self.setVisible(visible)

    @property
    def width(self):
        return self._pen.width()

    @width.setter
    def width(self, width):
        self._pen.setWidth(width)

    def itemChange(self, change, value):
        super().itemChange(change, value)

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
    
    def shape_from_path(self, path, pen):
        if path == QPainterPath() or pen == Qt.NoPen:
            return path

        ps = QPainterPathStroker()
        ps.setCapStyle(pen.capStyle())
        ps.setWidth(pen.widthF())
        ps.setJoinStyle(pen.joinStyle())
        ps.setMiterLimit(pen.miterLimit())

        p = ps.createStroke(path)
        p.addPath(path)
        return p

class PangoLabelGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._icon = "label"

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)

    def boundingRect(self):
        return super().boundingRect()

class PangoPathGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._icon = "path"
        self._points = []

    def add_point(self, pnt, action):
        self.prepareGeometryChange()
        self._points.append((pnt, action))

    def pop_point(self):
        self.prepareGeometryChange()
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

class PangoPolyGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._icon = "poly"
        self._points = []
        self._closed = False

        self.w = 10
        self._pen.setWidth(self.w)
        self._brush.setStyle(Qt.SolidPattern)

    @property
    def points(self):
        return self._points
    
    @points.setter
    def points(self, points):
        self._points = points
    
    @property
    def closed(self):
        return self._closed

    @closed.setter
    def closed(self, closed):
        self._closed = closed

    # TODO: Change these to property functions e.g += and -=
    def add_point(self, pnt):
        self.prepareGeometryChange()
        if len(self._points) > 1 and (QLineF(self._points[0], pnt).length() <= self.w):
            self._closed = True
        else:
            self._points.append(pnt)

    def rem_point(self):
        self.prepareGeometryChange()
        if len(self._points) > 1:
            self._points.pop()
            self._closed = False

    def move_point(self, point_idx, pos):
        self.prepareGeometryChange()
        self._points[point_idx] = pos
    
    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self._closed:
            painter.drawPolygon(QPolygonF(self._points))
        else:
            for n in range(0, len(self._points)-1):
                painter.drawLine(self._points[n], self._points[n+1])

        if option.state & QStyle.State_MouseOver:
            painter.setOpacity(1)
            for n in range(0, len(self._points)):
                painter.drawEllipse(self._points[n].x()-5,
                                 self._points[n].y()-5, 10, 10)

    def boundingRect(self):
        return self.shape().controlPointRect().adjusted(-self.w, -self.w, self.w, self.w)

    def shape(self):
        path = QPainterPath()
        path.addPolygon(QPolygonF(self._points))
        return self.shape_from_path(path, self._pen)

class PangoRectGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)

