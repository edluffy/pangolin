from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QPainter, QPainterPath, QStandardItem,
                         QStandardItemModel)
from PyQt5.QtWidgets import (QAction, QApplication, QMainWindow, QSizePolicy,
                             QTreeView, QWidget, QToolBar)

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
        self.menu_bar.open_images_action.triggered.connect(
            self.file_widget.open_images)

        # Layouts
        self.addDockWidget(Qt.LeftDockWidgetArea, self.label_widget)
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

        spacer_left = QWidget()
        spacer_right = QWidget()
        spacer_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.addAction(self.prefs_action)
        self.addWidget(spacer_left)
        self.addAction(self.open_images_action)
        self.addAction(self.import_labels_action)
        self.addAction(self.save_action)
        self.addAction(self.run_action)
        self.addWidget(spacer_right)
        self.addAction(self.filebar_action)
        self.addAction(self.labelbar_action)

window = MainWindow()
window.show()

app.exec_()
