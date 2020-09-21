from PyQt5.QtCore import QItemSelectionModel, QModelIndex, QRectF, Qt
from PyQt5.QtGui import QKeySequence, QPixmap, QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QMainWindow, QShortcut, QTreeView, QUndoView,
                             QVBoxLayout, QWidget)

from bar import PangoMenuBarWidget, PangoToolBarWidget
from dock import PangoFileWidget, PangoLabelWidget, PangoUndoWidget
from graphics import PangoGraphicsScene, PangoGraphicsView
from interface import PangoModelSceneInterface
from item import PangoLabelItem
app = QApplication([])
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Pangolin")
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setGeometry(50, 50, 1000, 675)

        # Models and Views
        self.interface = PangoModelSceneInterface()

        self.tree_view = QTreeView()
        self.tree_view.setUniformRowHeights(True)
        self.tree_view.setModel(self.interface.model)
        self.interface.set_tree(self.tree_view)

        self.graphics_view = PangoGraphicsView()
        self.graphics_view.setScene(self.interface.scene)

        self.undo_view = QUndoView()
        self.undo_view.setStack(self.interface.scene.undo_stack)

        # Dock widgets
        self.label_widget = PangoLabelWidget("Labels", self.tree_view)
        self.undo_widget = PangoUndoWidget("History", self.undo_view)
        self.file_widget = PangoFileWidget("Files")

        # Menu and toolbars
        self.menu_bar = PangoMenuBarWidget()
        self.tool_bar = PangoToolBarWidget()
        self.tool_bar.set_scene(self.interface.scene)
        self.tool_bar.label_select.setModel(self.interface.model)

        # Signals and Slots
        self.menu_bar.open_images_action.triggered.connect(self.file_widget.open)

        self.file_widget.file_view.activated.connect(self.switch_image)
        self.tool_bar.label_select.currentIndexChanged.connect(self.switch_label)

        # Layouts
        self.bg = QWidget()
        self.setCentralWidget(self.bg)

        self.bg_layout = QVBoxLayout(self.bg)
        self.bg_layout.setContentsMargins(0, 0, 0, 0)
        self.bg_layout.setSpacing(0)
        self.bg_layout.addWidget(self.tool_bar)
        self.bg_layout.addWidget(self.graphics_view)

        self.addDockWidget(Qt.RightDockWidgetArea, self.label_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.undo_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.file_widget)

        self.addToolBar(Qt.TopToolBarArea, self.menu_bar)

        # Shortcuts
        self.sh_reset_tool = QShortcut(QKeySequence('Esc'), self)
        #self.sh_reset_tool.activated.connect(self.scene.reset_tool)
        

    def switch_image(self, idx):
        fpath = idx.model().filePath(idx)
        self.interface.filter_tree(fpath)
        self.interface.scene.reset_com()
        self.interface.scene.fpath = fpath
        self.interface.scene.undo_stack.clear()
        self.interface.scene.setSceneRect(QRectF(QPixmap(fpath).rect()))
        self.graphics_view.fitInView(self.interface.scene.sceneRect(), Qt.KeepAspectRatio)

    def switch_label(self, row):
        item = self.interface.model.item(row)
        try:
            self.interface.scene.label = self.interface.map[item.key()]
            self.interface.scene.update_reticle()
            self.interface.scene.reset_com()
        except KeyError:
            return


window = MainWindow()
window.show()

app.exec_()
