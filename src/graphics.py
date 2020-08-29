from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import (QPainter, QPainterPath, QStandardItem,
                         QStandardItemModel, QPixmap, QPolygonF)
from PyQt5.QtWidgets import (QAbstractItemView, QApplication,
                             QGraphicsItemGroup, QGraphicsPathItem,
                             QGraphicsScene, QGraphicsView, QHBoxLayout,
                             QLabel, QMainWindow,
                             QTreeView, QGraphicsPixmapItem, QApplication)

from item import PangoHybridItem

# Model/View changes (item) ----> Scene/View (gfx)
class PangoGraphicsView(QAbstractItemView):
    tool_reset = pyqtSignal()
    
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
            if not hasattr(gfx, "p_index"):
                return
            if gfx.p_index() == idx:
                if roles[0] == Qt.DecorationRole:
                    gfx.set_decoration(color=idx.data(Qt.DecorationRole))

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

    def new_image(self, idx):
        path = idx.model().filePath(idx)

        for item in self.scene.items():
            if item.type == QGraphicsPixmapItem():
                self.scene.removeItem(item)
        new_item = self.scene.addPixmap(QPixmap(path))
        new_item.setZValue(-1)

# Scene/View changes (gfx) ----> Model/View (item)
class GraphicsScene(QGraphicsScene):
    tool_reset = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label_item = None # <---- get rid of this eventually
        self.current_item = None
        self.current_tool = None

        self.selectionChanged.connect(self.selection_changed)

    def selection_changed(self):
        if self.selectedItems() == []:
            self.parent().clearSelection()
            return

        s_idx = QtCore.QModelIndex(self.selectedItems()[0].p_index())
        self.parent().setCurrentIndex(s_idx)

    def reset_tool(self):
        self.tool_reset.emit()

    def change_tool(self, action):
        self.current_tool = action.text()

        px = QPixmap(QtCore.QSize(32, 32))
        px.fill(Qt.transparent)

        qp = QPainter(px)
        qp.setBrush(QtGui.QColor("blue"))
        qp.drawEllipse(0, 0, 30, 30)
        qp.end()

        cursor  = QtGui.QCursor(px)

        view = self.views()[0]
        if self.current_tool == "Pan":
            view.setCursor(Qt.OpenHandCursor)
        elif self.current_tool == "Path" or self.current_tool == "Filled Path":
            view.setCursor(cursor)
        elif self.current_tool == "Rect" or self.current_tool == "Poly":
            view.setCursor(Qt.CrossCursor)
        else:
            view.unsetCursor()

    def mousePressEvent(self, event):
        if self.label_item is None:
            return
        pos = event.scenePos()

        if self.current_tool == "Path" or self.current_tool == "Filled Path":
            self.current_item = PangoHybridItem(self.current_tool, self.label_item)
            path = QPainterPath(pos)
            self.current_item.data(Qt.UserRole).setPath(path)

        elif self.current_tool == "Poly":
            if self.current_item is None:
                self.current_item = PangoHybridItem(self.current_tool, self.label_item)
                poly = QPolygonF()
            else:
                poly = self.current_item.data(Qt.UserRole).polygon()

            if QtCore.QLineF(poly.first(), pos).length() <= 5:
                self.current_item.data(Qt.UserRole).close_poly(True)
                self.current_item = None
                self.tool_reset.emit()
            else:
                sub_item = PangoHybridItem("Dot", self.current_item)
                sub_item.data(Qt.UserRole).setRect(pos.x(), pos.y(), 5, 5)
                poly += sub_item.data(Qt.UserRole).rect().center()
                self.current_item.data(Qt.UserRole).setPolygon(poly)

        elif self.current_tool == "Select":
            super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        pos = event.scenePos()

        if self.current_tool == "Path" or self.current_tool == "Filled Path":
            if self.current_item is not None and event.buttons() & Qt.LeftButton:
                    path = self.current_item.data(Qt.UserRole).path()
                    path.lineTo(pos)
                    self.current_item.data(Qt.UserRole).setPath(path)

        elif self.current_tool == "Select":
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.current_tool == "Path" or self.current_tool == "Filled Path":
            if self.current_item is not None:
                    length = self.current_item.data(Qt.UserRole).path().length()
                    if length == 0:
                        idx = self.current_item.index()
                        self.current_item.model().removeRow(0, idx)
                    self.current_item = None

        elif self.current_tool == "Select":
            super().mouseReleaseEvent(event)

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
