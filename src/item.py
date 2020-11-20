from PyQt5.QtCore import QPointF, Qt, QRectF, QPersistentModelIndex
from PyQt5.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPainterPathStroker, QPen, QPolygonF, QStandardItem
from PyQt5.QtWidgets import QGraphicsItem, QStyle

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
        self.fpath = None
        self.color = QColor()

    def unique_row(self):
        root = self.model().invisibleRootItem()
        row = 0
        for i in range(0, root.rowCount()):
            if root.child(i).fpath == self.fpath:
                row+=1
        return row

class PangoPathItem(PangoItem):
    def __init__(self):
        super().__init__()
        self.path = PainterPath()

class PangoPolyItem(PangoItem):
    def __init__(self):
        super().__init__()
        self.poly = PolygonF()

class PangoBboxItem(PangoItem):
    def __init__(self):
        super().__init__()
        self.rect = QRectF()

class PangoGraphic(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

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

    def itemChange(self, change, value):
        super().itemChange(change, value)
        if self.scene() is not None:
            self.scene().gfx_changed.emit(self, change)
        return value

    def get_pen(self):
        pen = QPen()
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        if hasattr(self, "dynamic_width"):
            pen.setWidth(self.dynamic_width())
        elif hasattr(self, "path"):
            pen.setWidth(self.path.width)

        p_gfx = self.parentItem()
        if p_gfx is not None and hasattr(p_gfx, "color"):
            pen.setColor(p_gfx.color)
        return pen

    def get_brush(self):
        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)

        p_gfx = self.parentItem()
        if p_gfx is not None and hasattr(p_gfx, "color"):
            brush.setColor(p_gfx.color)
        return brush

    def paint(self, painter, option, widget):
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        if option.state & QStyle.State_Selected:
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
        self.fpath = None
        self.color = QColor()

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)

    def boundingRect(self):
        return QRectF()

class PangoPathGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.path = PainterPath()

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        painter.setPen(self.get_pen())
        painter.drawPath(self.path)

    def boundingRect(self):
        return self.shape().controlPointRect()

    def shape(self):
        st = QPainterPathStroker(self.get_pen())
        return st.createStroke(self.path)

class PangoPolyGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.poly = PolygonF()

    def dynamic_width(self):
        if self.scene() is not None:
            sz = self.scene().sceneRect().size()
            return (sz.width()+sz.height())/350
        return 10
    
    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        painter.setPen(self.get_pen())
        painter.setBrush(self.get_brush())

        if self.poly.isClosed():
            painter.drawPolygon(self.poly)
        else:
            for n in range(0, self.poly.count()-1):
                painter.drawLine(self.poly.value(n), self.poly.value(n+1))


        w = self.dynamic_width()
        if option.state & QStyle.State_MouseOver or not self.poly.isClosed():
            w += self.dynamic_width()/2

        painter.setOpacity(1)
        for n in range(0, self.poly.count()):
            painter.drawEllipse(self.poly.value(n), w/2, w/2)

    def boundingRect(self):
        w = self.dynamic_width()
        return self.shape().controlPointRect().adjusted(-w, -w, w, w)

    def shape(self):
        path = QPainterPath()
        path.addPolygon(self.poly)
        return self.shape_from_path(path, self.get_pen())

class PangoBboxGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rect = QRectF()

    def dynamic_width(self):
        if self.scene() is not None:
            sz = self.scene().sceneRect().size()
            return (sz.width()+sz.height())/500
        return 5

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        painter.setPen(self.get_pen())
        painter.setOpacity(0.8)

        painter.drawRect(self.rect)
        self.paint_text_rect(painter)

        painter.setOpacity(1)
        w = self.dynamic_width()
        if option.state & QStyle.State_MouseOver:
            w += self.dynamic_width()

        painter.drawEllipse(self.rect.topLeft(), w/2, w/2)
        painter.drawEllipse(self.rect.topRight(), w/2, w/2)
        painter.drawEllipse(self.rect.bottomLeft(), w/2, w/2)
        painter.drawEllipse(self.rect.bottomRight(), w/2, w/2)

    def paint_text_rect(self, painter):
        p = painter.pen()

        font = QFont()
        font.setPointSizeF(self.dynamic_width()*5)
        painter.setFont(font)
        painter.setBrush(self.get_brush())

        fm = QFontMetrics(font)
        w = fm.width(self.parentItem().name)
        h = fm.height()
        br = self.rect.bottomRight()

        text_rect = QRectF(QPointF(br.x()-w, br.y()-h), br)

        if text_rect.width() < self.boundingRect().width()/2 and\
                text_rect.height() < self.boundingRect().height()/2:
            painter.drawRect(text_rect)
            pen = self.get_pen()
            pen.setColor(QColor("black"))
            painter.setPen(pen)
            painter.drawText(text_rect, Qt.AlignCenter, self.parentItem().name)

        painter.setPen(p)

    def boundingRect(self):
        w = self.dynamic_width()
        return self.shape().controlPointRect().adjusted(-w, -w, w, w)

    def shape(self):
        path = QPainterPath()
        path.addRect(self.rect)
        return self.shape_from_path(path, self.get_pen())

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
