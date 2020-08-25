from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QPainter, QPainterPath, QStandardItem,
                         QStandardItemModel)
from PyQt5.QtWidgets import (QAbstractItemView, QApplication,
                             QGraphicsItemGroup, QGraphicsPathItem,
                             QGraphicsScene, QGraphicsView, QHBoxLayout,
                             QLabel, QMainWindow,
                             QTreeView)

from item import PangoHybridItem

# Model/View changes ----> Scene/View
class PangoGraphicsView(QAbstractItemView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = GraphicsScene()
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

            #if hasattr(ds_gfx, 'pen'):
            #    pen = ds_gfx.pen()
            #    color = pen.color()
            #    color.setAlphaF(1)
            #    pen.setColor(color)
            #    ds_gfx.setPen(pen)


    def dataChanged(self, top_left, bottom_right, roles):
        idx = top_left
        for gfx in self.scene.items():
            if gfx.data(0) == idx:
                if roles[0] == Qt.DecorationRole:
                    if hasattr(gfx, 'pen'):
                        pen = gfx.pen()
                        pen.setColor(idx.data(Qt.DecorationRole))
                        gfx.setPen(pen)

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



# Scene/View changes ----> Model/View
class GraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label_item = None
        self.current_item = None

        self.selectionChanged.connect(self.selection_changed)


    def selection_changed(self):
        if self.selectedItems() == []:
            return

    def mousePressEvent(self, event):
        if self.label_item is None:
            return
        pos = event.scenePos()

        self.current_item = PangoHybridItem("Path", self.label_item)
        path = QPainterPath(pos)
        self.current_item.data(Qt.UserRole).setPath(path)

    def mouseMoveEvent(self, event):
        pos = event.scenePos()

        if self.current_item is not None:
            path = self.current_item.data(Qt.UserRole).path()
            path.lineTo(pos)
            self.current_item.data(Qt.UserRole).setPath(path)

    def mouseReleaseEvent(self, event):
        if self.current_item is not None:
            self.current_item = None

class GraphicsView(QGraphicsView):
    def __init__ (self, parent=None):
        super().__init__(parent)

        self.setInteractive(True)
        self.setMouseTracking(True)

