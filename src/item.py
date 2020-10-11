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

        # Hidden Properties
        self._color = None
        self._icon = None
        self._width = None

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
    def visible(self):
        return self.data(Qt.CheckStateRole) == Qt.Checked

    @visible.setter
    def visible(self, state):
        self.setData(Qt.Checked if state else Qt.Unchecked, Qt.CheckStateRole)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color
        self.decorate()

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, icon):
        self._icon = icon
        self.decorate()

    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self, width):
        self._width = width

    def decorate(self):
        if self.parent() is not None:
            self._color = self.parent().color
        else:
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
        self._strokes = []

    @property
    def strokes(self):
        return self._strokes
    
    @strokes.setter
    def strokes(self, strokes):
        self._strokes = strokes

class PangoPolyItem(PangoItem):
    def __init__(self):
        super().__init__()
        self._icon = "poly"
        self._points = []
        self._closed = False

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

        # Hidden Properties
        self._fpath = None
        self._color = None
        self._icon = None
        self._width = None

        self.pen = QPen()
        self.pen.setCapStyle(Qt.RoundCap)
        self.pen.setJoinStyle(Qt.RoundJoin)
        self.brush = QBrush()
 
    @property
    def fpath(self):
        return self._fpath
    
    @fpath.setter
    def fpath(self, fpath):
        self._fpath = fpath

    @property
    def name(self):
        return self.toolTip()
    
    @name.setter
    def name(self, name):
        self.setToolTip(name)

    @property
    def visible(self):
        return self.isVisible()

    @visible.setter
    def visible(self, visible):
        self.setVisible(visible)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color
        self.pen.setColor(color)
        self.brush.setColor(color)

    @property
    def icon(self):
        return self._icon
    
    @icon.setter
    def icon(self, icon):
        self._icon = icon

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, width):
        self._width = width
        self.pen.setWidth(width)

    def decorate(self):
        if self.parentItem() is not None:
            self._color = self.parentItem().color
        else:
            idx = self.parentItem().childItems().index(self)
            self._color = pango_get_palette(idx)

    def setattrs(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    def itemChange(self, change, value):
        super().itemChange(change, value)

        if self.scene() is not None:
            self.scene().gfx_changed.emit(self, change)
        return value

    def paint(self, painter, option, widget):
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.setPen(self.pen)
        painter.setBrush(self.brush)

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
        self._strokes = []

    @property
    def strokes(self):
        return self._strokes
    
    @strokes.setter
    def strokes(self, strokes):
        self._strokes = strokes
    
    def path(self):
        if len(self._strokes) > 1:
            path = QPainterPath(self._strokes[0][0])
            for pos, motion in self._strokes[1:]:
                if motion == "line":
                    path.lineTo(pos)
                else:
                    path.moveTo(pos)
            return path
        else:
            return QPainterPath()

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        painter.drawPath(self.path())

    def boundingRect(self):
        return self.shape().controlPointRect()

    def shape(self):
        st = QPainterPathStroker(self.pen)
        return st.createStroke(self.path())

class PangoPolyGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._icon = "poly"
        self._points = []
        self._closed = None

        self.w = 10
        self.pen.setWidth(self.w)
        self.brush.setStyle(Qt.SolidPattern)

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
        return self.shape_from_path(path, self.pen)

class PangoRectGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)

