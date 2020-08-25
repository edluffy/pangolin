from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPointF, Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QPixmap, QPolygonF, QPainterPath, QPen, QStandardItem
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QGraphicsScene,
                             QGraphicsView, QLabel, QStackedLayout, QStyle,
                             QTabWidget, QGraphicsPolygonItem, QSizePolicy, QGraphicsPathItem, QGraphicsItem)

from widgets.utils import PangoToolBarWidget
from item import PangoStandardItem, PangoGraphicsPathItem

class PangoGraphicsScene(QGraphicsScene):
    dataChanged = pyqtSignal()
    rowsInserted = pyqtSignal(QGraphicsItem, QGraphicsItem)
    def __init__(self, item_map, parent=None):
        super().__init__(parent)
        self.item_map = item_map

        self.tool = None
        self.current_gfx_item = None

    def add_item(self, item, parent_gfx):
        self.addItem(item)
        self.rowsInserted.emit(item, parent_gfx)

    def mousePressEvent(self, event):
        if self.selectedItems() == []:
            return
        parent_gfx = self.selectedItems()[0]

        if self.tool == "Brush":
            gfx_item = PangoGraphicsPathItem(parent_gfx)
            self.add_item(gfx_item, parent_gfx)

            self.current_gfx_item = gfx_item
            path = QPainterPath(event.scenePos())
            self.current_gfx_item.setPath(path)

    def mouseMoveEvent(self, event):
        if self.tool == "Brush" and self.current_gfx_item is not None:
            path = self.current_gfx_item.path()
            path.lineTo(event.scenePos())
            self.current_gfx_item.setPath(path)

    def mouseReleaseEvent(self, event):
        if self.tool == "Brush" and self.current_gfx_item is not None:
            self.current_gfx_item.setOpacity(0.4)
            self.current_gfx_item = None

class PangoGraphicsView(QGraphicsView):
    def __init__ (self, parent=None):
        super(PangoGraphicsView, self).__init__ (parent)

    def wheelEvent(self, event):
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        zoom = 1.05

        old_pos = self.mapToScene(event.pos())
        if event.angleDelta().y() > 0:
            self.scale(zoom, zoom)
        else:
            self.scale(1/zoom, 1/zoom)
        new_pos = self.mapToScene(event.pos())

        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

