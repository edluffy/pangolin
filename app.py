from bidict import bidict

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QLabel, QLineEdit,
                             QListView, QMainWindow, QMenu, QPushButton,
                             QStatusBar, QVBoxLayout, QGraphicsItemGroup, QGraphicsPathItem)

from widgets.canvas import PangoCanvasWidget
from widgets.file import PangoFileWidget
from widgets.label import PangoLabelWidget
from widgets.utils import PangoMenuBarWidget

app = QApplication([])

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Pangolin")
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setGeometry(50, 50, 1000, 675)

        self.pango_item_map = bidict()

        # Toolbars and menus
        self.menu_bar = PangoMenuBarWidget()


        # Widgets
        self.label_widget = PangoLabelWidget("Labels", self.pango_item_map)
        self.file_widget = PangoFileWidget("Files")

        self.canvas_widget = PangoCanvasWidget(self.pango_item_map, self)

        self.file_widget.view.activated.connect(self.canvas_widget.new_tab)
        self.label_widget.labelChanged.connect(self.canvas_widget.label_changed)
        self.label_widget.model.dataChanged.connect(self.canvas_widget.data_changed)


        # Layouts
        #self.addToolBar(Qt.TopToolBarArea, self.menu_bar)
        self.addDockWidget(Qt.LeftDockWidgetArea,  self.label_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea,  self.file_widget)
        self.setCentralWidget(self.canvas_widget)

window = MainWindow()
window.show()

app.exec_()
