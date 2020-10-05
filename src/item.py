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

        self.props = {}
        self.props["name"] = ''
        self.props["fpath"] = ''
        self.props["icon"] = ''
        self.props["color"] = QColor()
        self.props["visible"] = bool
        self.props["width"] = float

        self.pen = QPen()
        self.pen.setCapStyle(Qt.RoundCap)
        self.pen.setJoinStyle(Qt.RoundJoin)
        self.brush = QBrush()
 
    @property
    def fpath(self):
        return self.props["fpath"]
    
    @fpath.setter
    def fpath(self, fpath):
        self.props["fpath"] = fpath
        # Hijack 'ItemMatrixChanged' since not being used anyway
        if self.scene() is not None:
            self.scene().gfx_changed.emit(self, QGraphicsItem.ItemMatrixChange)

    @property
    def name(self):
        return self.props["name"]
    
    @name.setter
    def name(self, name):
        self.props["name"] = name
        self.setToolTip(name)

    @property
    def color(self):
        return self.props["color"]

    @color.setter
    def color(self, color):
        if self.props["color"] != color:
            self.props["color"] = color
            self.pen.setColor(color)
            self.brush.setColor(color)
            if self.scene() is not None:
                # Hijack 'ItemTransformHasChanged' since not being used anyway
                self.scene().gfx_changed.emit(self, QGraphicsItem.ItemTransformHasChanged)

    @property
    def icon(self):
        return self.props["icon"]
    
    @icon.setter
    def icon(self, icon):
        if self.props["icon"] != icon:
            self.props["icon"] = icon
            if self.scene() is not None:
                # Hijack 'ItemTransformHasChanged' since not being used anyway
                self.scene().gfx_changed.emit(self, QGraphicsItem.ItemTransformHasChanged)

    @property
    def visible(self):
        return self.props["visible"]

    @visible.setter
    def visible(self, visible):
        self.props["visible"] = visible
        self.setVisible(visible)

    @property
    def width(self):
        return self.props["width"]

    @width.setter
    def width(self, width):
        self.props["width"] = width
        self.pen.setWidth(width)

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
        self.props["icon"] = "label"

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)

    def boundingRect(self):
        return super().boundingRect()

class PangoPathGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.props["icon"] = "path"
        self.props["strokes"] = []

    @property
    def strokes(self):
        return self.props["strokes"]
    
    @strokes.setter
    def strokes(self, strokes):
        self.props["strokes"] = strokes
    
    def path(self):
        if len(self.props["strokes"]) > 1:
            path = QPainterPath(self.props["strokes"][0][0])
            for pos, motion in self.props["strokes"][1:]:
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
        self.props["icon"] = "poly"
        self.props["points"] = []
        self.props["closed"] = False

        self.w = 10
        self.pen.setWidth(self.w)
        self.brush.setStyle(Qt.SolidPattern)

    @property
    def points(self):
        return self.props["points"]
    
    @points.setter
    def points(self, points):
        self.props["points"] = points
    
    @property
    def closed(self):
        return self.props["closed"]

    @closed.setter
    def closed(self, closed):
        self.props["closed"] = closed

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.props["closed"]:
            painter.drawPolygon(QPolygonF(self.props["points"]))
        else:
            for n in range(0, len(self.props["points"])-1):
                painter.drawLine(self.props["points"][n], self.props["points"][n+1])

        if option.state & QStyle.State_MouseOver:
            painter.setOpacity(1)
            for n in range(0, len(self.props["points"])):
                painter.drawEllipse(self.props["points"][n].x()-5,
                                 self.props["points"][n].y()-5, 10, 10)

    def boundingRect(self):
        return self.shape().controlPointRect().adjusted(-self.w, -self.w, self.w, self.w)

    def shape(self):
        path = QPainterPath()
        path.addPolygon(QPolygonF(self.props["points"]))
        return self.shape_from_path(path, self.pen)

class PangoRectGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)

