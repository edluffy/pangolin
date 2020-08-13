from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import (QApplication, QLabel, QLineEdit, QListView,
                             QMainWindow, QPushButton, QStatusBar, QVBoxLayout)

from widgets.dock import PangoFileWidget, PangoLabelWidget
from widgets.tab import PangoCanvasWidget

from models.node import *
from models.file import FileModel

app = QApplication([])


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Pangolin")
        self.setGeometry(50, 50, 1000, 675)

        # Test Data
        test_poly1 = QPolygonF([QPointF(10, 10), QPointF(
            20, 10), QPointF(20, 20), QPointF(10, 20)])
        test_poly2 = QPolygonF([QPointF(30, 30), QPointF(
            40, 30), QPointF(40, 40), QPointF(30, 40)])
        test_poly3 = QPolygonF([QPointF(50, 50), QPointF(
            60, 50), QPointF(60, 60), QPointF(50, 60)])
        test_poly4 = QPolygonF([QPointF(70, 70), QPointF(
            80, 70), QPointF(80, 80), QPointF(70, 80)])

        root_node = Node()

        label0   = GroupNode("breadboard", PALETTE[0], root_node)
        label0_0 = PolygonNode(label0)
        label0_1 = PolygonNode(label0)

        label1   = GroupNode("wire", PALETTE[1], root_node)
        label1_0 = PolygonNode(label1)

        label2   = GroupNode("push button", PALETTE[2], root_node)
        label2_0 = PolygonNode(label2)
        label2_1 = PixmapNode(label2)
        label2_2 = PolygonNode(label2)

        #label0   = GroupNode("breadboard", PALETTE[0], root_node)

        #label0   = GroupNode("breadboard", PALETTE[0], root_node)
        #label0_0 = PolygonNode(test_poly1, None, label0)
        #label0_1 = PolygonNode(test_poly2, None, label0)

        #label1   = GroupNode("wire", PALETTE[1], root_node)
        #label1_0 = PolygonNode(test_poly3, None, label1)

        #label2   = GroupNode("push button", PALETTE[2], root_node)
        #label2_0 = PolygonNode(test_poly4, None, label2)
        #label2_1 = PixmapNode(test_poly1, None, label2)
        #label2_2 = PolygonNode(test_poly2, None, label2)

        test_files = [
            '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/001.jpg',
            '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/002.jpg',
            '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/003.jpg',
            '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/004.jpg',
            '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/005.jpg',
            '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/006.jpg',
            '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/007.jpg',
            '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/008.jpg',
            '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/009.jpg',
            '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/010.jpg']

        # Toolbars and menus

        # Model and Views
        self.node_model = NodeModel(root_node)
        self.file_model = FileModel(test_files)

        # Widgets
        self.label_widget = PangoLabelWidget(self.node_model, "Labels")
        self.file_widget = PangoFileWidget(self.file_model, "Files")
        self.canvas_widget = PangoCanvasWidget(self.node_model)

        # Layouts
        self.addDockWidget(Qt.RightDockWidgetArea,  self.label_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea,  self.file_widget)
        self.setCentralWidget(self.canvas_widget)

window = MainWindow()
window.show()

app.exec_()
