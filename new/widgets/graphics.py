from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QPainter, QPainterPath, QStandardItem,
                         QStandardItemModel, QPixmap)
from PyQt5.QtWidgets import (QAbstractItemView, QApplication,
                             QGraphicsItemGroup, QGraphicsPathItem,
                             QGraphicsScene, QGraphicsView, QHBoxLayout,
                             QLabel, QMainWindow,
                             QTreeView, QGraphicsPixmapItem)

from item import PangoHybridItem

# Model/View changes (item) ----> Scene/View (gfx)
class PangoGraphicsView(QAbstractItemView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = GraphicsScene(self)
        self.view = GraphicsView(self.scene)

    def selectionChanged(self, selected, deselected):
        if selected.indexes() != []:
            s_idx = selected.indexes()[0]
            s_gfx = s_idx.data(Qt.UserRole)
            s_gfx.setSelected(True)

            while s_idx.parent().isValid():
                s_idx = s_idx.parent()
            self.scene.label_item = self.model().itemFromIndex(s_idx)

        if deselected.indexes() != []:
            ds_idx = deselected.indexes()[0]
            ds_gfx = ds_idx.data(Qt.UserRole)
            ds_gfx.setSelected(False)

    def dataChanged(self, top_left, bottom_right, roles):
        idx = top_left
        for gfx in self.scene.items():
            if gfx.data(0) == idx:
                if roles[0] == Qt.DecorationRole:
                    if hasattr(gfx, 'set_pen'):
                        gfx.set_pen(color=idx.data(Qt.DecorationRole))

                elif roles[0] == Qt.CheckStateRole:
                    visible = True if idx.data(
                        Qt.CheckStateRole) == Qt.Checked else False
                    gfx.setVisible(visible)


    def rowsInserted(self, parent_idx, start, end):
        idx = self.model().index(start, 0, parent_idx)
        gfx = idx.data(Qt.UserRole)

        parent_gfx = parent_idx.data(Qt.UserRole)
        if parent_gfx is None:
            self.scene.addItem(gfx)

    def rowsAboutToBeRemoved(self, parent_idx, start, end):
        idx = self.model().index(start, 0, parent_idx)
        gfx = idx.data(Qt.UserRole)

        self.scene.removeItem(gfx)
        del gfx

    def new(self, idx):
        path = idx.model().filePath(idx)

        for item in self.scene.items():
            if item.type == QGraphicsPixmapItem():
                self.scene.removeItem(item)
        new_item = self.scene.addPixmap(QPixmap(path))
        new_item.setZValue(-1)


# Scene/View changes (gfx) ----> Model/View (item)
class GraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label_item = None
        self.current_item = None

        self.selectionChanged.connect(self.selection_changed)

    def selection_changed(self):
        if self.selectedItems() == []:
            self.parent().clearSelection()
            return

        s_idx = QtCore.QModelIndex(self.selectedItems()[0].data(0))
        self.parent().setCurrentIndex(s_idx)


    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.label_item is None:
            return
        pos = event.scenePos()


    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if not event.buttons() & Qt.LeftButton:
            return

        pos = event.scenePos()

        if self.current_item is None:
            self.current_item = PangoHybridItem("Path", self.label_item)
            path = QPainterPath(pos)
            self.current_item.data(Qt.UserRole).setPath(path)
        else:
            path = self.current_item.data(Qt.UserRole).path()
            path.lineTo(pos)
            self.current_item.data(Qt.UserRole).setPath(path)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

        if self.current_item is not None:
            length = self.current_item.data(Qt.UserRole).path().length()
            if length == 0:
                idx = self.current_item.index()
                self.current_item.model().removeRow(0, idx)
            self.current_item = None

class GraphicsView(QGraphicsView):
    def __init__ (self, parent=None):
        super().__init__(parent)

        self.setInteractive(True)
        self.setMouseTracking(True)

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
