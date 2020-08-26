from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QPainter, QPainterPath, QStandardItem,
                         QStandardItemModel)
from PyQt5.QtWidgets import (QAction, QApplication, QMainWindow, QSizePolicy,
                             QTreeView, QWidget, QToolBar, QStatusBar, QLabel)

from widgets.dock import PangoFileWidget, PangoLabelWidget
from widgets.graphics import PangoGraphicsView

app = QApplication([])

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Pangolin")
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setGeometry(50, 50, 1000, 675)

        # Models and Views
        self.model = QStandardItemModel()
        self.model.removeRow

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)

        self.graphics_view = PangoGraphicsView()
        self.graphics_view.setModel(self.model)
        self.graphics_view.setSelectionModel(self.tree_view.selectionModel())

        # Dock widgets
        self.label_widget = PangoLabelWidget("Labels", self.tree_view)
        self.file_widget = PangoFileWidget("Files")

        # Menu and toolbars
        self.menu_bar = PangoMenuBarWidget()
        self.addToolBar(Qt.TopToolBarArea, self.menu_bar)

        self.status_bar = PangoStatusBarWidget()
        self.setStatusBar(self.status_bar)
        self.status_bar.view.setModel(self.model)

        # Signals and Slots
        self.file_widget.file_view.activated.connect(self.graphics_view.new)
        self.menu_bar.open_images_action.triggered.connect(
            self.file_widget.open)


        # Layouts
        self.addDockWidget(Qt.RightDockWidgetArea, self.label_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.file_widget)
        self.setCentralWidget(self.graphics_view.view)

class PangoMenuBarWidget(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        
        self.prefs_action = QAction("Preferences")
        self.open_images_action = QAction("Open Image Folder")
        self.import_labels_action = QAction("Import Labels")
        self.save_action = QAction("Save Masks")
        self.run_action = QAction("Run Inference")
        self.filebar_action = QAction("FileBar")
        self.labelbar_action = QAction("LabelBar")

        self.test1 = QAction("Pan")
        self.test2 = QAction("Select")
        self.test3 = QAction("Path")
        self.test4 = QAction("Rect")
        self.test5 = QAction("Poly")


        spacer_left = QWidget()
        spacer_right = QWidget()
        spacer_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.addAction(self.prefs_action)
        self.addAction(self.open_images_action)
        self.addAction(self.import_labels_action)
        self.addAction(self.save_action)
        self.addAction(self.run_action)

        self.addWidget(spacer_left)
        self.addAction(self.test1)
        self.addAction(self.test2)
        self.addAction(self.test3)
        self.addAction(self.test4)
        self.addAction(self.test5)
        self.addWidget(spacer_right)

        self.addAction(self.filebar_action)
        self.addAction(self.labelbar_action)

class PangoToolBarWidget(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Widgets
        self.pan_button = QPushButton("Pan")
        self.select_button = QPushButton("Select")
        self.path_button = QPushButton("Path")
        self.rect_button = QPushButton("Rect")
        self.poly_button = QPushButton("Poly")


        # Layouts
        self.layout = QGridLayout(self.bg)
        self.layout.addWidget(self.pan_button, 0, 0)
        self.layout.addWidget(self.select_button, 0, 1)
        self.layout.addWidget(self.path_button, 1, 0)
        self.layout.addWidget(self.rect_button, 1, 1)
        self.layout.addWidget(self.poly_button, 2, 0)

        self.button_group = QButtonGroup()
        for button in self.layout.children():
            self.button_group.addButton(button)

class PangoStatusBarWidget(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)

        self.view = QtWidgets.QComboBox()
        self.view.setFixedWidth(150)
        self.view.currentIndexChanged.connect(self.set_color)

        self.color_display = QLabel()
        self.color_display.setFixedWidth(150)

        self.addWidget(self.color_display)
        self.addWidget(self.view)

    def set_color(self, idx):
        color = self.view.itemData(idx, Qt.DecorationRole)
        if color is not None:
            self.color_display.setStyleSheet(
                "QLabel { background-color : "+color.name()+"}")



window = MainWindow()
window.show()

app.exec_()
