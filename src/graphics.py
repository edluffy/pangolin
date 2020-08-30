from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import (QPainter, QPainterPath, QPixmap, QPolygonF,
                         QStandardItem, QStandardItemModel)
from PyQt5.QtWidgets import (QAbstractItemView, QApplication,
                             QGraphicsEllipseItem, QGraphicsItemGroup,
                             QGraphicsPathItem, QGraphicsPixmapItem,
                             QGraphicsScene, QGraphicsView, QHBoxLayout,
                             QLabel, QMainWindow, QTreeView)

from item import PangoHybridItem


class PangoGraphicsView(QAbstractItemView):
    tool_reset = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = GraphicsScene(self)
        self.scene.selectionChanged.connect(self.scene_selection_changed)
        self.view = GraphicsView(self.scene)

    # Model/View changes (item) ----> Scene/View (gfx)
    def selectionChanged(self, selected, deselected):
        if selected.indexes() != []:
            s_idx = selected.indexes()[0]
            s_gfx = s_idx.data(Qt.UserRole)
            s_gfx.setSelected(True)

            while s_idx.parent().isValid():
                s_idx = s_idx.parent()

        if deselected.indexes() != []:
            ds_idx = deselected.indexes()[0]
            ds_gfx = ds_idx.data(Qt.UserRole)
            ds_gfx.setSelected(False)

    def dataChanged(self, top_left, bottom_right, roles):
        idx = top_left
        for gfx in self.scene.items():
            if hasattr(gfx, "p_index"):
                if gfx.p_index() == idx:
                    if roles[0] == Qt.DecorationRole:
                        gfx.set_decoration(color=idx.data(
                            Qt.DecorationRole), width=self.scene.current_tool_size)

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


    # Scene/View changes (gfx) ----> Model/View (item)
    def scene_selection_changed(self):
        if self.scene.selectedItems() == []:
            self.clearSelection()
        else:
            s_idx = QtCore.QModelIndex(self.scene.selectedItems()[0].p_index())
            self.setCurrentIndex(s_idx)


class GraphicsScene(QGraphicsScene):
    tool_reset = pyqtSignal()
    item_changed = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label_item = None # <----- Move to GraphicsView, create item, return gfx
        self.current_item = None # <--- Replace with current_gfx implementation
        self.current_tool = None
        self.current_tool_size = 10
        self.init_reticle(10)

    def init_reticle(self, size):
        self.reticle_item = QGraphicsEllipseItem()
        self.reticle_item.setVisible(False)
        self.reticle_item.setOpacity(0.8)
        self.reticle_item.setRect(-size/2, -size/2, size, size)
        self.reticle_item.setPen(QtGui.QPen(Qt.PenStyle.NoPen))
        self.addItem(self.reticle_item)

    def preview_reticle(self, entered, widget_pos):
        if entered:
            view = self.views()[0]
            pos = QtCore.QPoint()

            pos.setX(widget_pos.x())
            pos.setY(view.viewport().geometry().top())
            pos = view.mapToScene(pos)
            pos.setY(pos.y()+self.reticle_item.rect().width()/2)

            self.reticle_item.setPos(pos)
            self.reticle_item.setVisible(True)
        else:
            self.reticle_item.setVisible(False)

    def reset_tool(self):
        self.tool_reset.emit()

    def change_image(self, idx):
        path = idx.model().filePath(idx)

        for item in self.items():
            if item.type == QGraphicsPixmapItem():
                self.removeItem(item)
        new_item = self.addPixmap(QPixmap(path))
        new_item.setZValue(-1)

    def change_label(self, row):
        self.label_item = self.parent().model().item(row)
        if self.label_item is not None:
            color = self.label_item.data(Qt.DecorationRole)
            if color is not None:
                self.reticle_item.setBrush(QtGui.QBrush(color, Qt.SolidPattern))

    def change_tool(self, action):
        self.current_tool = action.text()
        self.reticle_item.setVisible(False)

        view = self.views()[0]
        if self.current_tool == "Path" or self.current_tool == "Filled Path":
            view.setCursor(Qt.BlankCursor)
            self.reticle_item.setVisible(True)
        elif self.current_tool == "Pan":
            view.setCursor(Qt.OpenHandCursor)
        elif self.current_tool == "Rect" or self.current_tool == "Poly":
            view.setCursor(Qt.CrossCursor)
        else:
            view.unsetCursor()

    def change_tool_size(self, size):
        self.current_tool_size = size
        self.reticle_item.setRect(-size/2, -size/2, size, size)

    def set_current_item(self, item):
        self.current_item = item
        if item is not None:
            text = item.type
        else:
            text = ""
        self.item_changed.emit(text)

    def mousePressEvent(self, event):
        if self.label_item is None:
            return
        pos = event.scenePos()

        if self.current_tool == "Path" or self.current_tool == "Filled Path":
            item = PangoHybridItem(self.current_tool, self.label_item)
            self.set_current_item(item)
            path = QPainterPath(pos)
            self.current_item.data(Qt.UserRole).setPath(path)

        elif self.current_tool == "Poly":
            if self.current_item is None:
                item = PangoHybridItem(self.current_tool, self.label_item)
                self.set_current_item(item)
                poly = QPolygonF()
            else:
                poly = self.current_item.data(Qt.UserRole).polygon()

            if QtCore.QLineF(poly.first(), pos).length() <= 5:
                self.current_item.data(Qt.UserRole).close_poly(True)
                self.set_current_item(None)
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

            self.reticle_item.setPos(pos)

        elif self.current_tool == "Select":
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.current_tool == "Path" or self.current_tool == "Filled Path":
            if self.current_item is not None:
                length = self.current_item.data(Qt.UserRole).path().length()
                if length == 0:
                    idx = self.current_item.index()
                    self.current_item.model().removeRow(0, idx)
                self.set_current_item(None)

        elif self.current_tool == "Select":
            super().mouseReleaseEvent(event)

class GraphicsView(QGraphicsView):
    cursor_moved = pyqtSignal(QtCore.QPoint)
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

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        scene_pos = self.mapToScene(event.pos()).toPoint()
        self.cursor_moved.emit(scene_pos)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.scene().reticle_item.setVisible(False)

    def enterEvent(self, event):
        super().enterEvent(event)
        tool = self.scene().current_tool
        if tool == "Path" or tool == "Filled Path":
            self.scene().reticle_item.setVisible(True)

