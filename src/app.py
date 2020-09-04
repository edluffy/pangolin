from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QStandardItemModel
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView, QVBoxLayout, QWidget, QShortcut

from bar import PangoMenuBarWidget, PangoToolBarWidget
from dock import PangoFileWidget, PangoLabelWidget
from graphics import PangoSceneModelInterface, PangoGraphicsScene, PangoGraphicsView

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
        self.interface = PangoSceneModelInterface(self.model)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setSelectionMode(QTreeView.ExtendedSelection)
        self.tree_view.setStyleSheet(
            "QTreeView::indicator:checked:enabled{ image: url(:black/eye_on.png)} \
             QTreeView::indicator:unchecked{ image: url(:black/eye_off.png)}")

        self.graphics_scene = PangoGraphicsScene()

        self.graphics_view = PangoGraphicsView()
        self.graphics_view.setScene(self.graphics_scene)

        self.interface.set_view(self.tree_view)
        self.interface.set_scene(self.graphics_scene)

        # Dock widgets
        self.label_widget = PangoLabelWidget("Labels", self.tree_view)
        self.file_widget = PangoFileWidget("Files")

        # Menu and toolbars
        self.menu_bar = PangoMenuBarWidget()
        self.tool_bar = PangoToolBarWidget()
        self.tool_bar.label_select.setModel(self.model)

        # Signals and Slots
        self.menu_bar.open_images_action.triggered.connect(
            self.file_widget.open)

        self.file_widget.file_view.activated.connect(
            self.graphics_scene.change_image)

        self.tool_bar.label_select.currentIndexChanged.connect(
            self.interface.set_label)

        self.tool_bar.action_group.triggered.connect(
            self.graphics_scene.change_tool)
        self.tool_bar.size_select.valueChanged.connect(
            self.graphics_scene.set_tool_size)

        self.graphics_scene.tool_reset.connect(self.tool_bar.reset_tool)
        self.graphics_scene.views()[0].cursor_moved.connect(self.tool_bar.update_coords)

        # Layouts
        self.bg = QWidget()
        self.setCentralWidget(self.bg)

        self.bg_layout = QVBoxLayout(self.bg)
        self.bg_layout.setContentsMargins(0, 0, 0, 0)
        self.bg_layout.setSpacing(0)
        self.bg_layout.addWidget(self.tool_bar)
        self.bg_layout.addWidget(self.graphics_view)

        self.addDockWidget(Qt.RightDockWidgetArea, self.label_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.file_widget)

        self.addToolBar(Qt.TopToolBarArea, self.menu_bar)

        # Shortcuts
        self.sh_reset_tool = QShortcut(QKeySequence('Esc'), self)
        self.sh_reset_tool.activated.connect(self.graphics_scene.reset_tool)


window = MainWindow()
window.show()

app.exec_()
