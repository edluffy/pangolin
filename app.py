from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPainterPath
from PyQt5.QtWidgets import (QApplication, QLabel, QLineEdit, QListView,
                             QMainWindow, QPushButton, QStatusBar, QVBoxLayout, QMenu)

from widgets.utils import PangoMenuBarWidget
from widgets.file import PangoFileWidget
from widgets.label import PangoLabelWidget
from widgets.canvas import PangoCanvasWidget

app = QApplication([])


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Pangolin")
        self.setUnifiedTitleAndToolBarOnMac(True)
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

        # Toolbars and menus
        self.menu_bar = PangoMenuBarWidget()

        # Model and Views

        # Widgets
        self.label_widget = PangoLabelWidget("Labels")
        self.file_widget = PangoFileWidget("Files")

        self.canvas_widget = PangoCanvasWidget(
            self.file_widget.s_model, self.label_widget.s_model, self)
        self.file_widget.view.doubleClicked.connect(self.canvas_widget.new_tab)

        # Layouts
        self.addToolBar(Qt.TopToolBarArea, self.menu_bar)
        self.addDockWidget(Qt.RightDockWidgetArea,  self.label_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea,  self.file_widget)
        self.setCentralWidget(self.canvas_widget)

window = MainWindow()
window.show()

app.exec_()
