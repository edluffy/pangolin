import os, pickle
from src.converters.image_mask import image_mask_write
from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (QApplication, QFileDialog, QMainWindow, QMessageBox, QShortcut, QTreeView, QUndoStack, QUndoView, QVBoxLayout, QWidget)

from src.bar import PangoMenuBarWidget, PangoToolBarWidget
from src.converters.pascal_voc import pascal_voc_read, pascal_voc_write
from src.converters.yolo import yolo_read, yolo_write
from src.dock import PangoFileWidget, PangoLabelWidget, PangoUndoWidget
from src.dialog import ExportSettingsDialog, ImportSettingsDialog
from src.graphics import PangoGraphicsView
from src.interface import PangoModelSceneInterface

app = QApplication([])
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pangolin")
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setGeometry(50, 50, 1200, 675)

        # Models and Views
        self.interface = PangoModelSceneInterface()

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
        self.menu_bar.export_action.triggered.connect(self.export_project)
        self.menu_bar.import_action.triggered.connect(self.import_project)
        self.menu_bar.save_project_action.triggered.connect(self.save_project)

        self.file_widget.file_view.selectionModel().currentChanged.connect(self.switch_image)
        self.file_widget.file_model.directoryLoaded.connect(self.after_loaded_images)
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
        self.sh_reset_tool.activated.connect(self.tool_bar.reset_tool)

        self.sh_inc_tool_size = QShortcut(QKeySequence(Qt.SHIFT+Qt.Key_Underscore), self)
        self.sh_inc_tool_size.activated.connect(
                lambda: self.tool_bar.set_tool_size(1, additive=True))

        self.sh_dec_tool_size = QShortcut(QKeySequence(Qt.SHIFT+Qt.Key_Equal), self)
        self.sh_dec_tool_size.activated.connect(
                lambda: self.tool_bar.set_tool_size(-1, additive=True))

        self.sh_select_next_image = QShortcut(QKeySequence(Qt.CTRL+Qt.Key_Down), self)
        self.sh_select_next_image.activated.connect(self.file_widget.select_next_image)

        self.sh_select_prev_image = QShortcut(QKeySequence(Qt.CTRL+Qt.Key_Up), self)
        self.sh_select_prev_image.activated.connect(self.file_widget.select_prev_image)

        self.sh_select_next_label = QShortcut(QKeySequence(Qt.CTRL+Qt.Key_Right), self)
        self.sh_select_next_label.activated.connect(
                self.tool_bar.label_select.select_next_label)

        self.sh_select_prev_label = QShortcut(QKeySequence(Qt.CTRL+Qt.Key_Left), self)
        self.sh_select_prev_label.activated.connect(
                self.tool_bar.label_select.select_prev_label)
        
        self.sh_undo = QShortcut(QKeySequence(Qt.CTRL+Qt.Key_Z), self)
        self.sh_undo.activated.connect(self.undo_widget.undo)

        self.sh_redo = QShortcut(QKeySequence(Qt.CTRL+Qt.Key_Y), self)
        self.sh_redo.activated.connect(self.undo_widget.redo)


    def switch_image(self, c_idx, p_idx):
        c_fpath = self.file_widget.file_model.filePath(c_idx)
        p_fpath = self.file_widget.file_model.filePath(p_idx)

        self.interface.scene.set_fpath(c_fpath)
        self.interface.scene.reset_com()
        self.graphics_view.fitInView(self.interface.scene.sceneRect(), Qt.KeepAspectRatio)

        # Handling unsaved changes
        if c_fpath not in self.interface.scene.change_stacks.keys():
            self.interface.scene.change_stacks[c_fpath] = QUndoStack()
        self.undo_view.setStack(self.interface.scene.change_stacks[c_fpath])
        self.interface.scene.stack = self.interface.scene.change_stacks[c_fpath]
        self.interface.filter_tree(c_fpath, p_fpath)

    def load_images(self, action=None, fpath=None):
        if fpath is None:
            dialog = QFileDialog()
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            fpath = QFileDialog.getExistingDirectory()
        
        if fpath != "":
            self.file_widget.file_model.setRootPath(fpath)
            root_idx = self.file_widget.file_model.index(fpath)
            self.file_widget.file_view.setRootIndex(root_idx)
            self.images_are_new = True

    def after_loaded_images(self):
        if self.images_are_new is True:
            folder_path = self.file_widget.file_model.rootPath()
            for f in sorted(os.listdir(folder_path)):
                if f.endswith(".jpg") or f.endswith(".png"):
                    idx = self.file_widget.file_model.index(os.path.join(folder_path, f))
                    self.file_widget.file_view.setCurrentIndex(idx)
                    break

            self.file_widget.file_view.scrollToTop()
            self.load_project()
            self.images_are_new = False

    def save_project(self, action=None, project_path=None):
        if project_path is None:
            project_path = os.path.join(
                    self.file_widget.file_model.rootPath(), "pangolin_project.p")

        pickle_items = []
        for k in self.interface.map.keys():
            pickle_items.append(self.interface.model.itemFromIndex(QModelIndex(k)))
        pickle.dump(pickle_items, open(project_path, "wb"))

    def load_project(self, action=None, project_path=None):
        if project_path is None:
            project_path = os.path.join(
                    self.file_widget.file_model.rootPath(), "pangolin_project.p")

        if os.path.exists(project_path):

            # Clear project
            self.interface.map.clear()
            self.interface.model.clear()
            self.interface.scene.full_clear()

            unpickled_items = pickle.load(open(project_path, "rb"))
            for item in unpickled_items:
                if item.parent() is None:
                    self.interface.model.appendRow(item)
                item.force_update()

            self.interface.filter_tree(self.interface.scene.fpath, None)

    def export_project(self, action=None):
        folder_path = self.file_widget.file_model.rootPath()

        fpaths = self.interface.scene.change_stacks.keys()
        dialog = ExportSettingsDialog(self, fpaths)
        if dialog.exec():
            s_fpaths = dialog.selected_fnames()
            file_format = dialog.file_format()

            if file_format == "PascalVOC (XML)":
                for fpath in s_fpaths:
                    pascal_voc_write(self.interface, fpath)

            elif file_format == "COCO (JSON)":
                #export_fpath, _ = QFileDialog().getSaveFileName(
                #    self, "Save Project", os.path.join(default, "annotations.xml"),
                #    "XML files (*.xml)")
                pass

            elif file_format == "YOLOv3 (TXT)":
                for fpath in s_fpaths:
                    yolo_write(self.interface, fpath)

            elif file_format == "Image Mask (PNG)":
                mask_folder = os.path.join(folder_path, "Masks")
                if not os.path.exists(mask_folder):
                    os.mkdir(mask_folder)
                for fpath in s_fpaths:
                    idx = self.file_widget.file_model.index(fpath)
                    self.file_widget.file_view.setCurrentIndex(idx)
                    image_mask_write(self.interface, fpath, mask_folder)

            self.interface.filter_tree(self.interface.scene.fpath, None)

    def import_project(self, action=None, folder=None):
        if folder is None:
            folder = self.file_widget.file_model.rootPath()
        fpaths = []
        for fname in os.listdir(folder):
            pre, ext = os.path.splitext(fname)
            if ext in (".xml", ".txt"):
                fpaths.append(os.path.join(folder, fname))
        if fpaths == []:
            return

        dialog = ImportSettingsDialog(self, fpaths)
        if dialog.exec():
            s_fpaths = dialog.selected_fnames()

            for fpath in s_fpaths:
                pre, ext = os.path.splitext(fpath)
                if ext == ".xml": # PascalVOC (XML)
                    pascal_voc_read(self.interface, fpath)
                elif ext == ".txt":
                    yolo_read(self.interface, fpath)

    def unsaved_files_dialog(self):
        #if pfile != "":
        #    # Save changes?
        #    if self.interface.map:
        #        result = self.unsaved_files_dialog()
        #        if result == QMessageBox.Cancel:
        #            return
        #        elif result == QMessageBox.Save:
        #            self.save_project()

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
            for stack in self.interface.scene.change_stacks.values():
                stack.clear()
        return res

    def export_warning_dialog(self):
        pass

window = MainWindow()
window.show()

app.exec_()
