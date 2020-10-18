import os
from PyQt5.QtCore import QFile, QIODevice, QItemSelectionModel, QModelIndex, QPointF, QRectF, QXmlStreamWriter, Qt
from PyQt5.QtGui import QColor, QKeySequence, QPixmap, QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QFileDialog, QMainWindow, QMessageBox, QShortcut, QTreeView, QUndoView,
                             QVBoxLayout, QWidget)

from bar import PangoMenuBarWidget, PangoToolBarWidget
from dock import PangoFileWidget, PangoLabelWidget, PangoUndoWidget
from graphics import PangoGraphicsScene, PangoGraphicsView
from interface import PangoModelSceneInterface
from item import PangoGraphic, PangoLabelGraphic, PangoLabelItem
from xml_handler import Xml_Handler
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

        # Serialisation
        self.x_handler = Xml_Handler(self.interface.model)

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
        self.menu_bar.open_images_action.triggered.connect(self.load_images)
        self.menu_bar.save_action.triggered.connect(self.save_project)
        self.menu_bar.load_action.triggered.connect(self.load_project)

        self.file_widget.file_view.selectionModel().currentChanged.connect(self.switch_image)
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
        
    def save_project(self):
        folder_path = self.file_widget.file_model.rootPath()
        if folder_path != "." and os.path.exists(folder_path):
            dialog = QMessageBox()
            dialog.setText("Pango project file exists, overwrite?")
            dialog.setInformativeText("Located at: "+folder_path)
            dialog.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            dialog.setDefaultButton(QMessageBox.Save)

            if dialog.exec() == QMessageBox.Save:
                self.x_handler.write(folder_path+"/pango.xml")

    def load_project(self):
        folder_path = self.file_widget.file_model.rootPath()
        if folder_path != ".":
            if os.path.exists(folder_path+"/pango.xml"):
                dialog = QMessageBox()
                dialog.setText("Existing pango project file found in image folder, load?")
                dialog.setInformativeText("Located at: "+folder_path)
                dialog.setStandardButtons(QMessageBox.Open | QMessageBox.Close)
                dialog.setDefaultButton(QMessageBox.Open)

                if dialog.exec() == QMessageBox.Open:
                    self.x_handler.read(folder_path+"/pango.xml")
                    return

        dialog = QFileDialog()
        dialog.setDefaultSuffix("xml")
        dialog.exec()

        if dialog.result():
            print(dialog.directory().absolutePath())

            self.interface.map.clear()
            self.interface.model.clear()
            self.interface.scene.full_clear()

            #self.x_handler.read(path+"/pango.xml")
            self.switch_label(0)

    def load_images(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.DirectoryOnly)

        if dialog.exec():
            folder_path = dialog.directory().absolutePath()

            self.file_widget.file_model.setRootPath(folder_path)
            root_idx = self.file_widget.file_model.index(folder_path)

            self.file_widget.file_view.setRootIndex(root_idx)
            #self.file_widget.file_view.selectionModel().setCurrentIndex(
            #        self.file_widget.file_view.rootIndex(), QItemSelectionModel.Select)
            #self.file_widget.file_view.rootIndex()

            if os.path.exists(folder_path+"/pango.xml"):
                dialog = QMessageBox()
                dialog.setText("Existing Project found in image folder, load?")
                dialog.setInformativeText("Located at: "+folder_path)
                dialog.setStandardButtons(QMessageBox.Open | QMessageBox.Close)
                dialog.setDefaultButton(QMessageBox.Open)

                if dialog.exec() == QMessageBox.Open:
                    self.x_handler.read(folder_path+"/pango.xml")

    def switch_image(self, c_idx, p_idx):
        fpath = self.file_widget.file_model.filePath(c_idx)
        self.interface.filter_tree(fpath)
        self.interface.scene.reset_com()
        self.interface.scene.fpath = fpath
        self.interface.scene.undo_stack.clear()
        self.interface.scene.setSceneRect(QRectF(QPixmap(fpath).rect()))
        self.graphics_view.fitInView(self.interface.scene.sceneRect(), Qt.KeepAspectRatio)

    def switch_label(self, row):
        item = self.interface.model.item(row)
        if item is None:
            return
        try:
            self.interface.scene.label = self.interface.map[item.key()]
            self.interface.scene.update_reticle()
            self.interface.scene.reset_com()
        except KeyError:
            return

window = MainWindow()
window.show()

app.exec_()
