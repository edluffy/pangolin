from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import (QApplication, QVBoxLayout, QLabel, QLineEdit,
                             QListView, QMainWindow, QPushButton, QStatusBar)

from widgets.label import PangoLabelWidget
from widgets.file import PangoFileWidget
from widgets.canvas import PangoCanvasWidget

app = QApplication([])


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Pangolin")
        self.setGeometry(50, 50, 1000, 675)

        # Toolbars and menus

        # Widgets
        self.label_widget = PangoLabelWidget("Labels")
        self.file_widget = PangoFileWidget("Files")
        self.canvas_widget = PangoCanvasWidget()

        # Layouts
        self.addDockWidget(Qt.RightDockWidgetArea,  self.label_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea,  self.file_widget)
        self.setCentralWidget(self.canvas_widget)

window = MainWindow()
window.show()

app.exec_()
