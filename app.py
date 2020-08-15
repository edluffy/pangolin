from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPainterPath
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

        test_layers = [
                (QColor("green"), 'breaboard', True, QPainterPath()), 
                (QColor("red"), 'resistor', True, QPainterPath()), 
                (QColor("yellow"), 'capacitor', False, QPainterPath()), 
                (QColor("blue"), 'chip', True, QPainterPath()), 
                ]

        # Toolbars and menus

        # Model and Views
        self.layer_model = LayerModel(test_layers)
        self.layer_selection = QtCore.QItemSelectionModel(self.layer_model)

        self.file_model = FileModel(test_files)

        # Widgets
        self.label_widget = PangoLabelWidget(self.layer_selection, "Labels")
        self.canvas_widget = PangoCanvasWidget(self.layer_selection, self)

        self.file_widget = PangoFileWidget(self.file_model, "Files")

        # Layouts
        self.addDockWidget(Qt.RightDockWidgetArea,  self.label_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea,  self.file_widget)
        self.setCentralWidget(self.canvas_widget)

window = MainWindow()
window.show()

app.exec_()
