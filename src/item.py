from PyQt5.QtCore import QPointF, Qt, QRectF, QPersistentModelIndex, QModelIndex
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
                self._icon = "rectangle"
            elif self.type() == PangoShapeType.Poly:
                self._icon = "polygon"
            elif self.type() == PangoShapeType.Dot:
                self._icon = "dot"
            else:
                self._icon = "path"

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
        self.setFlag(QGraphicsItem.ItemIsMovable)

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
                self._icon = "rectangle"
            elif self.type() == PangoShapeType.Poly:
                self._icon = "polygon"
            elif self.type() == PangoShapeType.Dot:
                self._icon = "dot"
            else:
                self._icon = "path"

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
            if self.opacity() != 1:
                self.setOpacity(1)
        else:
            if self.opacity() != 0.5:
                self.setOpacity(0.5)

    def boundingRect(self):
        return QRectF()

    def type(self):
        return PangoShapeType.Default

class PangoPathGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._path  = QPainterPath()

    def set_width(self, width=None):
        if width is not None:
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
        outline = st.createStroke(self._path)
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
