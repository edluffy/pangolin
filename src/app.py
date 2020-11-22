import os, pickle
from os.path import basename
from PyQt5.QtCore import QDir, QFile, QIODevice, QItemSelectionModel, QModelIndex, QPoint, QPointF, QRectF, QXmlStreamWriter, Qt
from PyQt5.QtGui import QColor, QKeySequence, QPixmap, QStandardItemModel
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDialog, QFileDialog, QFileSystemModel, QHBoxLayout, QInputDialog, QLabel, QListWidget, QMainWindow, QMessageBox, QPushButton, QShortcut, QTreeView, QUndoStack, QUndoView,
                             QVBoxLayout, QWidget)

from bar import PangoMenuBarWidget, PangoToolBarWidget
from converters.pascal_voc import pascal_voc_write
from converters.yolo import yolo_write
from dialog import ExportSettingsDialog
from dock import PangoFileWidget, PangoLabelWidget, PangoUndoWidget
from graphics import PangoGraphicsScene, PangoGraphicsView
from interface import PangoModelSceneInterface
from item import PangoBboxItem, PangoGraphic, PangoLabelGraphic, PangoLabelItem
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
        self.menu_bar.export_action.triggered.connect(self.export_project)

        self.file_widget.file_view.selectionModel().currentChanged.connect(self.switch_image)
        self.file_widget.file_model.directoryLoaded.connect(self.select_first_image)
        self.tool_bar.label_select.currentIndexChanged.connect(self.interface.switch_label)
        self.tool_bar.del_labels_signal.connect(self.interface.del_labels)

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

        self.interface.copy_labels(c_fpath, p_fpath)
        self.interface.filter_tree(c_fpath, p_fpath)
        self.tool_bar.filter_label_select(c_fpath)

    def select_first_image(self):
        fpath = self.file_widget.file_model.rootPath()
        for f in sorted(os.listdir(fpath)):
            if f.endswith(".jpg") or f.endswith(".png"):
                idx = self.file_widget.file_model.index(os.path.join(fpath, f))
                self.file_widget.file_view.setCurrentIndex(idx)
                return

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
                item.force_update()

            # Open image folder
            for item in unpickled_items:
                if hasattr(item, "fpath"):
                    fpath = os.path.dirname(item.fpath)
                    self.file_widget.file_model.setRootPath(fpath)
                    root_idx = self.file_widget.file_model.index(fpath)
                    self.file_widget.file_view.setRootIndex(root_idx)
                    break

    def export_project(self, action=None):
        default = self.file_widget.file_model.rootPath()

        fpaths = self.change_stacks.keys()
        items_by_fpath = {}
        for fpath in fpaths:
            items_by_fpath[fpath] = [item for item in self.interface.find_in_tree(
                "fpath", fpath, 1, True) if type(item) != PangoLabelItem]

        dialog = ExportSettingsDialog(self, items_by_fpath.keys())
        if dialog.exec():
            s_fpaths = dialog.selected_fnames()
            file_format = dialog.file_format()

            if file_format == "PascalVOC (XML)":
                for fpath in s_fpaths:
                    if items_by_fpath[fpath] != []:
                        pascal_voc_write(self.interface, items_by_fpath[fpath], fpath)

            elif file_format == "COCO (JSON)":
                #export_fpath, _ = QFileDialog().getSaveFileName(
                #    self, "Save Project", os.path.join(default, "annotations.xml"),
                #    "XML files (*.xml)")
                pass

            elif file_format == "YOLOv3 (TXT)":
                for fpath in s_fpaths:
                    if items_by_fpath[fpath] != []:
                        yolo_write(self.interface, items_by_fpath[fpath], fpath)

            elif file_format == "Image Mask (PNG)":
                pass


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
