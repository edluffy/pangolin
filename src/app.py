import os, pickle
from PyQt5.QtCore import QDir, QFile, QIODevice, QItemSelectionModel, QModelIndex, QPointF, QRectF, QXmlStreamWriter, Qt
from PyQt5.QtGui import QColor, QKeySequence, QPixmap, QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QFileDialog, QFileSystemModel, QMainWindow, QMessageBox, QShortcut, QTreeView, QUndoStack, QUndoView,
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
        self.setGeometry(50, 50, 1200, 675)

        # Models and Views
        self.interface = PangoModelSceneInterface()
        self.change_stacks = {}

        self.tree_view = QTreeView()
        self.tree_view.setUniformRowHeights(True)
        self.tree_view.setModel(self.interface.model)
        self.interface.set_tree(self.tree_view)

        self.graphics_view = PangoGraphicsView()
        self.graphics_view.setScene(self.interface.scene)

        self.undo_view = QUndoView()

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
        self.interface.scene.clear_changes.connect(self.unsaved_commands_dialog)

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
        
    def switch_label(self, row):
        item = self.interface.model.item(row)
        if item is not None:
            try:
                self.interface.scene.active_label = self.interface.map[item.key()]
            except KeyError:
                return

            self.interface.scene.update_reticle()
            self.interface.scene.reset_com()

    def switch_image(self, c_idx, p_idx):
        c_fpath = self.file_widget.file_model.filePath(c_idx)
        p_fpath = self.file_widget.file_model.filePath(p_idx)

        self.interface.scene.fpath = c_fpath
        self.interface.scene.reset_com()
        self.interface.scene.setSceneRect(QRectF(QPixmap(c_fpath).rect()))
        self.graphics_view.fitInView(self.interface.scene.sceneRect(), Qt.KeepAspectRatio)

        # Handling unsaved changes
        if c_fpath not in self.change_stacks.keys():
            self.change_stacks[c_fpath] = QUndoStack()
        self.undo_view.setStack(self.change_stacks[c_fpath])
        self.interface.scene.stack = self.change_stacks[c_fpath]

        self.interface.copy_labels_tree(c_fpath, p_fpath)
        self.interface.filter_tree(c_fpath, p_fpath)
        self.tool_bar.filter_label_select(c_fpath)

    def load_images(self, action=None, fpath=None):
        if fpath is None:
            dialog = QFileDialog()
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            fpath = QFileDialog.getExistingDirectory()
        
        if fpath != "":
            self.file_widget.file_model.setRootPath(fpath)
            root_idx = self.file_widget.file_model.index(fpath)
            self.file_widget.file_view.setRootIndex(root_idx)

    def save_project(self, action=None, pfile=None):
        if pfile is None:
            pf = os.path.join(self.file_widget.file_model.rootPath(), "pango_project.p")
            if os.path.exists(pf):
                pfile = pf

        if pfile is None:
            default = self.file_widget.file_model.rootPath()+"/pango_project.p"
            pfile, _ = QFileDialog().getSaveFileName(
                self, "Save Project", default, "Pickle files (*.p)")

        if pfile != "":
            pickle_items = []
            for k in self.interface.map.keys():
                pickle_items.append(self.interface.model.itemFromIndex(QModelIndex(k)))
            pickle.dump(pickle_items, open(pfile, "wb"))

    def load_project(self, action=None, pfile=None):
        if pfile is None:
            pfile, _ = QFileDialog().getOpenFileName(
                    self, caption="Load Project", filter="Pickle files (*.p)")
        
        if pfile != "":
            # Save changes?
            if self.interface.map:
                result = self.unsaved_files_dialog()
                if result == QMessageBox.Cancel:
                    return
                elif result == QMessageBox.Save:
                    self.save_project()

            # Clear project
            self.interface.map.clear()
            self.interface.model.clear()
            self.interface.scene.full_clear()
            self.file_widget.file_view.setRootIndex(QModelIndex())

            unpickled_items = pickle.load(open(pfile, "rb"))
            for item in unpickled_items:
                if item.parent() is None:
                    self.interface.model.appendRow(item)
                self.interface.item_changed(item.index(), None, None)

            # Open image folder
            for item in unpickled_items:
                if hasattr(item, "fpath"):
                    fpath = os.path.dirname(item.fpath)
                    self.file_widget.file_model.setRootPath(fpath)
                    root_idx = self.file_widget.file_model.index(fpath)
                    self.file_widget.file_view.setRootIndex(root_idx)
                    break


    def unsaved_files_dialog(self):
        dialog = QMessageBox()
        dialog.setText("The project has been modified.")
        dialog.setInformativeText("Do you want to save your changes?")
        dialog.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        dialog.setDefaultButton(QMessageBox.Save)
        return dialog.exec()

    def unsaved_commands_dialog(self):
        res = QMessageBox().question(self.parent(), "Unsaved shape commands", 
                "Command history will be cleaned, are you sure you want to continue?")
        if res == QMessageBox.Yes:
            for stack in self.change_stacks.values():
                stack.clear()
        return res


    def export_warning_dialog(self):
        pass

window = MainWindow()
window.show()

app.exec_()
