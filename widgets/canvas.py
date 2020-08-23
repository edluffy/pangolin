from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter, QPixmap, QPolygonF, QPainterPath, QPen, QStandardItem
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QGraphicsScene,
                             QGraphicsView, QLabel, QStackedLayout, QStyle,
                             QTabWidget, QGraphicsPolygonItem, QSizePolicy, QGraphicsPathItem, QGraphicsItem)

from widgets.utils import PangoToolBarWidget
from item import PangoStandardItem, PangoGraphicsPathItem

class PangoCanvasWidget(QTabWidget):
    def __init__(self, item_map, parent=None):
        super().__init__(parent)
        self.item_map = item_map

        # Toolbars and menus
        self.tool_bar = PangoToolBarWidget()
        self.parentWidget().addToolBar(Qt.LeftToolBarArea, self.tool_bar)

        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)


    def new_tab(self, idx):
        title = idx.data(Qt.DisplayRole)
        path = idx.data(Qt.ToolTipRole)
        #opened = self.file_model.data(idx, Qt.UserRole+1)

        self.canvas = Canvas(self.item_map)
        self.canvas.addPixmap(QPixmap(path))
        self.view = MyQGraphicsView(self.canvas)
        self.view.setInteractive(True)

        self.addTab(self.view, QApplication.style().standardIcon(
            QStyle.SP_ComputerIcon), title)

        self.tool_bar.action_group.triggered.connect(self.canvas.tool_changed)

    def label_changed(self, label_std_item):
        self.canvas.label_std_item = label_std_item
        self.canvas.label_gfx_item = self.item_map[label_std_item.map_index()]

    def data_changed(self, top_left, bottom_right, role):
        pass


class Canvas(QGraphicsScene):
    def __init__(self, item_map, parent=None):
        super().__init__(parent)
        self.item_map = item_map
        self.label_std_item = None
        self.label_gfx_item = None

        self.tool = None
        self.current_gfx_item = None

    def create_gfx_path(self):
        std_item = PangoStandardItem("Path", self.label_std_item)
        gfx_item = PangoGraphicsPathItem(self.label_gfx_item)
        self.item_map[std_item.map_index()] = gfx_item

        gfx_item.pen().setColor(std_item.data(Qt.DecorationRole))

        self.addItem(gfx_item)
        self.current_gfx_item = gfx_item

    def mousePressEvent(self, event):
        if self.label_std_item is None:
            return

        if self.tool == "Brush":
            self.create_gfx_path()
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

    def tool_changed(self, action):
        self.tool = action.text()


class MyQGraphicsView(QGraphicsView):
    def __init__ (self, parent=None):
        super(MyQGraphicsView, self).__init__ (parent)

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

