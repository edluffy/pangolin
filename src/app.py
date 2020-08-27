from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QPainter, QPainterPath, QStandardItem,
                         QStandardItemModel, QIcon)
from PyQt5.QtWidgets import (QAction, QApplication, QMainWindow, QSizePolicy,
                             QTreeView, QWidget, QToolBar, QStatusBar, QLabel, QActionGroup)

from resources import icons_rc
from widgets.dock import PangoFileWidget, PangoLabelWidget
from widgets.graphics import PangoGraphicsView

app = QApplication([])
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

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
        self.tree_view.setStyleSheet(
                "QTreeView::indicator:checked:enabled{ image: url(:black/eye_on.png)} \
                        QTreeView::indicator:unchecked{ image: url(:black/eye_off.png)}")

        self.graphics_view = PangoGraphicsView()
        self.graphics_view.setModel(self.model)
        self.graphics_view.setSelectionModel(self.tree_view.selectionModel())

        # Dock widgets
        self.label_widget = PangoLabelWidget("Labels", self.tree_view)
        self.file_widget = PangoFileWidget("Files")

        # Menu and toolbars
        self.menu_bar = PangoMenuBarWidget()
        self.addToolBar(Qt.TopToolBarArea, self.menu_bar)

        self.tool_bar = PangoToolBarWidget()
        self.addToolBar(Qt.LeftToolBarArea, self.tool_bar)

        self.status_bar = PangoStatusBarWidget()
        self.setStatusBar(self.status_bar)
        self.status_bar.view.setModel(self.model)

        # Signals and Slots
        self.file_widget.file_view.activated.connect(self.graphics_view.new_image)
        self.menu_bar.open_images_action.triggered.connect(
            self.file_widget.open)
        self.tool_bar.action_group.triggered.connect(
            self.graphics_view.new_tool)


        # Layouts
        self.addDockWidget(Qt.RightDockWidgetArea, self.label_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.file_widget)
        self.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.setCentralWidget(self.graphics_view.view)

class PangoMenuBarWidget(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setIconSize(QtCore.QSize(16, 16))
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        self.prefs_action = QAction("Preferences")
        self.prefs_action.setIcon(QIcon(":/black/prefs.png"))

        self.open_images_action = QAction("Open Image Folder")
        self.open_images_action.setIcon(QIcon(":/black/add_images.png"))

        self.import_labels_action = QAction("Import Labels")
        self.import_labels_action.setIcon(QIcon(":/black/add_label.png"))

        self.save_action = QAction("Save Masks")
        self.save_action.setIcon(QIcon(":/black/save.png"))

        self.run_action = QAction("PyTorch")
        self.run_action.setIcon(QIcon(":/black/torch.png"))

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

class PangoToolBarWidget(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setIconSize(QtCore.QSize(16, 16))

        self.pan_action = QAction("Pan")
        self.pan_action.setIcon(QIcon(":/black/pan.png"))

        self.select_action = QAction("Select")
        self.select_action.setIcon(QIcon(":/black/select.png"))

        self.path_action = QAction("Path")
        self.path_action.setIcon(QIcon(":/black/brush.png"))

        self.rect_action = QAction("Rect")
        self.rect_action.setIcon(QIcon(":/black/rect.png"))

        self.poly_action = QAction("Poly")
        self.poly_action.setIcon(QIcon(":/black/poly.png"))


        self.action_group = QActionGroup(self)
        self.action_group.setExclusive(True)
        self.action_group.addAction(self.pan_action)
        self.action_group.addAction(self.select_action)
        self.action_group.addAction(self.path_action)
        self.action_group.addAction(self.rect_action)
        self.action_group.addAction(self.poly_action)

        for action in self.action_group.actions():
            action.setCheckable(True)
        self.addActions(self.action_group.actions())

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
