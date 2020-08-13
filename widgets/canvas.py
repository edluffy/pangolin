from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPixmap, QPolygonF
from PyQt5.QtWidgets import (QApplication, QGraphicsScene, QLabel,
                             QStackedLayout, QStyle, QTabWidget, QAbstractItemView)

from widgets.dock import PangoDockWidget

class PangoCanvasWidget(QTabWidget):
    def __init__(self, *args, **kwargs):
        super(PangoCanvasWidget, self).__init__(*args, **kwargs)

        # Test Data

        # Model and Views
        self.view = CanvasView()

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

class CanvasView(QAbstractItemView):
    def __init__(self, *args, **kwargs):
        super(CanvasView, self).__init__(*args, **kwargs)

        test_poly = QPolygonF([QPointF(10, 10), QPointF(
            20, 10), QPointF(20, 20), QPointF(10, 20)])

        self.Shape
