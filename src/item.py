from PyQt5.QtCore import QPointF, Qt, QRectF, QPersistentModelIndex
from PyQt5.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPainterPathStroker, QPen, QPolygonF, QStandardItem, QTransform
from PyQt5.QtWidgets import QAbstractGraphicsShapeItem, QGraphicsItem, QStyle

from utils import pango_get_icon


class PangoItem(QStandardItem):
    def __init__ (self):
        super().__init__()
        self.setCheckable(True)
        self.setEditable(False)

        self.visible = True

    def key(self):
        return QPersistentModelIndex(self.index())

    def children(self):
        return [self.child(i) for i in range(0, self.rowCount())]
    
    def setattrs(self, **kwargs):
        for k, v in kwargs.items():
            if v != getattr(self, k):
                setattr(self, k, v)

    def getattrs(self):
        return {
            k: getattr(self, k) 
            for k in ["name", "visible", "fpath", "color", 
                "path", "width", "poly", "rect"] 
            if hasattr(self, k)
        }

    def force_update(self):
        if self.model() is not None:
            self.model().dataChanged.emit(self.index(), self.index(), [Qt.UserRole])
    
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

    def set_icon(self):
        icon = type(self).__name__.replace("Pango", "").replace("Item", "").lower()
        p_item = self.parent()

        if hasattr(self, "color"):
            self.setData(pango_get_icon(icon, self.color), Qt.DecorationRole)
        elif p_item is not None and hasattr(p_item, "color"):
            self.setData(pango_get_icon(icon, p_item.color), Qt.DecorationRole)

    def __getstate__(self):
        return {
            **self.getattrs(),
            '_PangoItem__parent': self.parent()
        }

    def __setstate__(self, state):
        self.__init__()
        parent = state['_PangoItem__parent']
        if parent is not None:
            parent.appendRow(self)

        del state['_PangoItem__parent']
        self.setattrs(**state)
        self.set_icon()

class PangoLabelItem(PangoItem):
    def __init__(self):
        super().__init__()
        self.color = QColor()

class PangoPathItem(PangoItem):
    def __init__(self):
        super().__init__()
        self.fpath = None
        self.path = PainterPath()

class PangoPolyItem(PangoItem):
    def __init__(self):
        super().__init__()
        self.fpath = None
        self.poly = PolygonF()

class PangoBboxItem(PangoItem):
    def __init__(self):
        super().__init__()
        self.fpath = None
        self.rect = QRectF()

class PangoGraphic(QAbstractGraphicsShapeItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setAcceptHoverEvents(True)
        self.force_opaque = False

        pen = QPen()
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)

        self.setPen(pen)
        self.setBrush(brush)

    def setattrs(self, **kwargs):
        for k, v in kwargs.items():
            if v != getattr(self, k):
                setattr(self, k, v)

    def getattrs(self):
        return {
            k: getattr(self, k) 
            for k in ["name", "visible", "fpath", "color", 
                "width", "path", "poly", "rect"] 
            if hasattr(self, k)
        }

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

    def dw(self):
        rect = QRectF(self.scene().px.rect())
        if rect != QRectF():
            return (rect.size().height()+rect.size().width())/400
        else:
            return 10
    
    def inherit_color(self):
        if hasattr(self.parentItem(), "color"):
            pen = self.pen()
            brush = self.brush()
            pen.setColor(self.parentItem().color)
            brush.setColor(self.parentItem().color)
            self.setPen(pen)
            self.setBrush(brush)

    def itemChange(self, change, value):
        super().itemChange(change, value)
        if self.scene() is not None:
            self.scene().gfx_changed.emit(self, change)
        return value

    def paint(self, painter, option, widget):
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        if self.force_opaque:
            painter.setOpacity(1)
        elif option.state & QStyle.State_Selected:
            painter.setOpacity(0.7)
        else:
            painter.setOpacity(0.5)

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

    def __getstate__(self):
        return {
            **self.getattrs(),
            '_PangoGraphic__parent': self.parentItem()
        }

    def __setstate__(self, state):
        self.__init__()
        parent = state['_PangoGraphic__parent']
        if parent is not None:
            self.setParentItem(parent)
            
        del state['_PangoGraphic__parent']
        self.setattrs(**state)

class PangoLabelGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemClipsChildrenToShape)

    @property
    def color(self):
        return self.pen().color()

    @color.setter
    def color(self, color):
        pen = self.pen()
        pen.setColor(color)
        brush = self.brush()
        brush.setColor(color)

        self.setPen(pen)
        self.setBrush(brush)
        for item in self.childItems():
            item.setPen(pen)
            item.setBrush(brush)

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)

    def boundingRect(self):
        return QRectF(self.scene().px.rect())

class PangoPathGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.fpath = None
        self.path = PainterPath()

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        pen = self.pen()
        pen.setWidth(self.path.width)
        painter.setPen(pen)

        painter.drawPath(self.path)

    def boundingRect(self):
        return self.shape().controlPointRect()

    def shape(self):
        pen = self.pen()
        pen.setWidth(self.path.width)
        st = QPainterPathStroker(pen)
        return st.createStroke(self.path)

class PangoPolyGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.fpath = None
        self.poly = PolygonF()

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)

        w = self.dw()
        pen = self.pen()
        pen.setWidth(int(w))
        painter.setPen(pen)
        painter.setBrush(self.brush())

        # Draw Polygon/Polyline
        if self.poly.isClosed():
            painter.drawPolygon(self.poly)
        else:
            for n in range(0, self.poly.count()-1):
                painter.drawLine(self.poly.value(n), self.poly.value(n+1))

        # Draw points
        if option.state & QStyle.State_MouseOver or self.isSelected()\
                or not self.poly.isClosed() or self.poly.count() == 1:
            painter.setOpacity(1)
            for n in range(0, self.poly.count()):
                painter.drawEllipse(self.poly.value(n), w, w)

    def boundingRect(self):
        w = self.dw()
        return self.shape().controlPointRect().adjusted(-w, -w, w, w)

    def shape(self):
        path = QPainterPath()
        path.addPolygon(self.poly)
        return self.shape_from_path(path, self.pen())

class PangoBboxGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.fpath = None
        self.rect = QRectF()

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        w = self.dw()
        pen = self.pen()
        pen.setWidth(int(w))
        painter.setPen(pen)

        if not self.force_opaque:
            painter.setOpacity(0.8)
        painter.drawRect(self.rect)

        if self.parentItem() is not None:
            self.paint_text_rect(painter)

        painter.setOpacity(1)
        if option.state & QStyle.State_MouseOver or self.isSelected():
            painter.drawEllipse(self.rect.topLeft(), w, w)
            painter.drawEllipse(self.rect.topRight(), w, w)
            painter.drawEllipse(self.rect.bottomLeft(), w, w)
            painter.drawEllipse(self.rect.bottomRight(), w, w)

    def paint_text_rect(self, painter):
        p = painter.pen()

        font = QFont()
        font.setPointSizeF(self.dw()*3)
        painter.setFont(font)
        painter.setBrush(self.brush())

        fm = QFontMetrics(font)
        w = fm.width(self.parentItem().name)
        h = fm.height()
        br = self.rect.bottomRight()

        text_rect = QRectF(QPointF(br.x()-w, br.y()-h), br)

        if text_rect.width() < self.boundingRect().width()/2 and\
                text_rect.height() < self.boundingRect().height()/2:
            painter.drawRect(text_rect)
            pen = self.pen()
            pen.setColor(QColor("black"))
            painter.setPen(pen)
            painter.drawText(text_rect, Qt.AlignCenter, self.parentItem().name)

        painter.setPen(p)

    def boundingRect(self):
        w = self.dw()
        return self.shape().controlPointRect().adjusted(-w*2, -w*2, w*2, w*2)

    def shape(self):
        path = QPainterPath()
        path.addRect(self.rect)
        return self.shape_from_path(path, self.pen())

class PainterPath(QPainterPath):
    def __init__(self):
        super().__init__()
        self.width = None

    def __getstate__(self):
        d = {}
        d["width"] = self.width
        for i in range(0, self.elementCount()):
            ele = self.elementAt(i)
            d[i] = [ele.type, ele.x, ele.y]
        return d

    def __setstate__(self, state):
        self.__init__()
        self.width = state["width"]
        del state["width"]

        for k, v in state.items():
            if v[0]==0:
                self.moveTo(v[1], v[2])
            if v[0]==1:
                self.lineTo(v[1], v[2])

class PolygonF(QPolygonF):
    def __init__(self):
        super().__init__()

    def __getstate__(self):
        d = {}
        for i in range(0, self.count()):
            pos = self.value(i)
            d[i] = [pos.x(), pos.y()]
        return d

    def __setstate__(self, state):
        self.__init__()
        for k, v in state.items():
            self.append(QPointF(v[0], v[1]))
