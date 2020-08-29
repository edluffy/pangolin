from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QAction, QActionGroup, QLabel, QSizePolicy,
                             QStatusBar, QToolBar, QWidget)


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
        
        self.filled_path_action = QAction("Filled Path")

        self.rect_action = QAction("Rect")
        self.rect_action.setIcon(QIcon(":/black/rect.png"))

        self.poly_action = QAction("Poly")
        self.poly_action.setIcon(QIcon(":/black/poly.png"))


        self.action_group = QActionGroup(self)
        self.action_group.setExclusive(True)

        self.action_group.addAction(self.pan_action)
        self.action_group.addAction(self.select_action)
        self.action_group.addAction(self.path_action)
        self.action_group.addAction(self.filled_path_action)
        self.action_group.addAction(self.rect_action)
        self.action_group.addAction(self.poly_action)

        for action in self.action_group.actions():
            action.setCheckable(True)
        self.addActions(self.action_group.actions())

    def reset_tool(self):
        self.select_action.setChecked(True)
        self.action_group.triggered.emit(self.select_action)

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
