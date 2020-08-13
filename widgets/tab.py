from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter, QPixmap, QPolygonF
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QGraphicsScene,
                             QGraphicsView, QLabel, QStackedLayout, QStyle,
                             QTabWidget, QGraphicsPolygonItem)


class PangoCanvasWidget(QTabWidget):
    def __init__(self, model, parent=None):
        super().__init__(parent)

        # Model and Views
        self.model = model

        self.scene = CanvasScene(model)
        self.view = QGraphicsView(self.scene)

        # Toolbars and menus
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)

        # Widgets
        example_label = QLabel("hey")
        example_label2 = QLabel("lol")

        # Layouts
        self.addTab(self.view, QApplication.style().standardIcon(
            QStyle.SP_ComputerIcon), "003.jpg")

        self.addTab(example_label, QApplication.style().standardIcon(
            QStyle.SP_FileDialogNewFolder), "001.jpg")

        self.addTab(example_label2, QApplication.style().standardIcon(
            QStyle.SP_ComputerIcon), "002.jpg")

class CanvasScene(QGraphicsScene):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self._model = model

        self._model.dataChanged.connect(self.data_changed)

    def data_changed(self, top_left, bottom_right, role):
        self.addItem(self._model.node_from_index(top_left))
