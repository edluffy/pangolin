from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QIcon, QPainter, QPainterPath, QStandardItem,
                         QStandardItemModel)
from PyQt5.QtWidgets import (QAction, QActionGroup, QApplication, QLabel,
                             QMainWindow, QSizePolicy, QStatusBar, QToolBar,
                             QTreeView, QWidget)

from bar import PangoMenuBarWidget, PangoStatusBarWidget, PangoToolBarWidget
from dock import PangoFileWidget, PangoLabelWidget
from graphics import PangoGraphicsView
from resources import icons_rc

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
        self.tool_bar = PangoToolBarWidget()
        self.status_bar = PangoStatusBarWidget()
        self.status_bar.view.setModel(self.model)


        # Signals and Slots
        self.file_widget.file_view.activated.connect(
            self.graphics_view.new_image)
        self.menu_bar.open_images_action.triggered.connect(
            self.file_widget.open)

        self.tool_bar.action_group.triggered.connect(
            self.graphics_view.scene.change_tool)
        self.graphics_view.scene.tool_reset.connect(self.tool_bar.reset_tool)

        # Layouts
        self.addToolBar(Qt.TopToolBarArea, self.menu_bar)
        self.addToolBar(Qt.LeftToolBarArea, self.tool_bar)
        self.setStatusBar(self.status_bar)

        self.addDockWidget(Qt.RightDockWidgetArea, self.label_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.file_widget)
        self.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.setCentralWidget(self.graphics_view.view)


window = MainWindow()
window.show()

app.exec_()
