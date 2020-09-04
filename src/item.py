from PyQt5.QtCore import Qt, QRectF, QPersistentModelIndex, QModelIndex
from PyQt5.QtGui import QBrush, QColor, QPainterPath, QPainterPathStroker, QPen, QPolygonF, QStandardItem
from PyQt5.QtWidgets import (QAbstractGraphicsShapeItem, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem,
                             QGraphicsPolygonItem, QGraphicsRectItem, QStyle)

from utils import PangoShapeType, pango_get_palette

class PangoHybridItem(QStandardItem):
    def __init__ (self, type):
        super().__init__()
        self.set_type(type)
        self.setCheckable(True)

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
    
    def color(self):
        return QColor(self.data(Qt.DecorationRole))

    def set_color(self, color=None):
        self.setData(color, Qt.DecorationRole)
    
    def colorize(self):
        if self.parent() is None:
            self.set_color(pango_get_palette(self.row()))
        else:
            self.set_color(self.parent().color())

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
        self.setFlag(QGraphicsItem.ItemIsMovable)

        self._pen = QPen()
        self._pen.setWidth(10)
        self._pen.setCapStyle(Qt.RoundCap)
        self._pen.setJoinStyle(Qt.RoundJoin)

        self._brush = QBrush()
 
    def name(self):
        return self.toolTip()
    
    def set_name(self, name):
        self.setToolTip(name)

    def color(self):
        return self._pen.color()

    def set_color(self, color):
        self._pen.setColor(color)
        # Hijack 'ItemTransformHasChanged' since not being used
        if self.scene() is not None:
            self.scene().gfx_changed.emit(self, QGraphicsItem.ItemTransformHasChanged)

    def colorize(self):
        if self.parentItem() is None:
            self.set_color(pango_get_palette(len(self.scene().items())))
        else:
            self.set_color(self.parentItem().color())

    def visible(self):
        return self.isVisible()

    def set_visible(self, state):
        self.setVisible(state)

    def itemChange(self, change, value):
        if self.scene() is not None:
            self.scene().gfx_changed.emit(self, change)
        return value

    def paint(self, painter, option, widget):
        painter.setPen(self._pen)
        painter.setBrush(self._brush)

        if option.state & QStyle.State_Selected:
            self.setOpacity(1)
        else:
            self.setOpacity(0.5)

    def boundingRect(self):
        return QRectF()

    def type(self):
        return PangoShapeType.Default

class PangoPathGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._path  = QPainterPath()

    def set_width(self, width):
        self._pen.setWidth(width)

    def move_to(self, pnt):
        self._path.moveTo(pnt)
        self.update()

    def line_to(self, pnt):
        self._path.lineTo(pnt)
        self.update()

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        painter.drawPath(self._path)

    def boundingRect(self):
        return self.shape().controlPointRect()

    def shape(self):
        st = QPainterPathStroker(self._pen)
        st.setWidth(self._pen.width()*1.5)
        outline = st.createStroke(self._path).simplified()
        return outline

    def type(self):
        return PangoShapeType.Path

class PangoPolyGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)


class PangoRectGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)


class PangoDotGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
