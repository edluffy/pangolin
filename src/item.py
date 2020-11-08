from PyQt5.QtCore import Qt, QRectF, QPersistentModelIndex
from PyQt5.QtGui import QBrush, QColor, QPainter, QPainterPath, QPainterPathStroker, QPen, QPolygonF, QStandardItem
from PyQt5.QtWidgets import QGraphicsItem, QStyle

from utils import pango_get_icon

class PangoItem(QStandardItem):
    def __init__ (self):
        super().__init__()
        self.setCheckable(True)
        self.setEditable(False)

    def key(self):
        return QPersistentModelIndex(self.index())

    def setattrs(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

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

        if hasattr(self, "color"):
            self.setData(pango_get_icon(icon, self.color), Qt.DecorationRole)
        else:
            p_item = self.parent()
            if p_item is not None:
                if hasattr(p_item, "color"):
                    self.setData(pango_get_icon(icon, p_item.color), Qt.DecorationRole)

class PangoLabelItem(PangoItem):
    def __init__(self):
        super().__init__()
        self.fpath = None
        self.color = QColor()

class PangoPathItem(PangoItem):
    def __init__(self):
        super().__init__()
        self.strokes = []
        self.width = 0

class PangoPolyItem(PangoItem):
    def __init__(self):
        super().__init__()
        self.points = []
        self.closed = False

class PangoRectItem(PangoItem):
    def __init__(self):
        super().__init__()

class PangoGraphic(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

    def setattrs(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    @property
    def name(self):
        return self.toolTip()

    @name.setter
    def name(self, visible):
        self.setToolTip(visible)

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
        if hasattr(self, "width"):
            pen.setWidth(self.width)
        else:
            pen.setWidth(10) # Temp - change this to scale with qgraphicsview

        p_gfx = self.parentItem()
        if p_gfx is not None:
            if hasattr(p_gfx, "color"):
                pen.setColor(p_gfx.color)
        return pen

    def get_brush(self):
        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)

        p_gfx = self.parentItem()
        if p_gfx is not None:
            if hasattr(p_gfx, "color"):
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
        self.strokes = []
        self.width = 0

    def path(self):
        if len(self.strokes) > 1:
            path = QPainterPath(self.strokes[0][0])
            for pos, motion in self.strokes[1:]:
                if motion == "line":
                    path.lineTo(pos)
                else:
                    path.moveTo(pos)
            return path
        else:
            return QPainterPath()


    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        painter.setPen(self.get_pen())
        painter.drawPath(self.path())

    def boundingRect(self):
        return self.shape().controlPointRect()

    def shape(self):
        st = QPainterPathStroker(self.get_pen())
        return st.createStroke(self.path())

class PangoPolyGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []
        self.closed = False

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        painter.setPen(self.get_pen())
        painter.setBrush(self.get_brush())

        if self.closed:
            painter.drawPolygon(QPolygonF(self.points))
        else:
            for n in range(0, len(self.points)-1):
                painter.drawLine(self.points[n], self.points[n+1])

        if self.isSelected():
            painter.setOpacity(1)
            for n in range(0, len(self.points)):
                painter.drawEllipse(self.points[n].x()-5,
                                 self.points[n].y()-5, 10, 10)

    def boundingRect(self):
        w = self.width
        return self.shape().controlPointRect().adjusted(-w, -w, w, w)

    def shape(self):
        path = QPainterPath()
        path.addPolygon(QPolygonF(self.points))
        return self.shape_from_path(path, self.get_pen())

class PangoRectGraphic(PangoGraphic):
    def __init__(self, parent=None):
        super().__init__(parent)

