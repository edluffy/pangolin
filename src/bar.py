from PyQt5.QtCore import QPoint, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (QAction, QActionGroup, QColorDialog, QComboBox,
                             QLabel, QSizePolicy, QSpinBox, QStatusBar, QStyle, QStyleOptionComboBox,
                             QToolBar, QWidget)

from item import PangoLabelItem
from utils import pango_get_icon


class PangoMenuBarWidget(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setIconSize(QSize(24, 24))
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        # Widgets
        spacer_left = QWidget()
        spacer_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer_right = QWidget()
        spacer_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Actions
        self.prefs_action = QAction("Prefs")
        self.open_images_action = QAction("Open Images")
        self.import_labels_action = QAction("Import Labels")
        self.save_action = QAction("Save Masks")
        self.run_action = QAction("PyTorch")

        self.action_group = QActionGroup(self)
        self.action_group.addAction(self.prefs_action)
        self.action_group.addAction(self.open_images_action)
        self.action_group.addAction(self.import_labels_action)
        self.action_group.addAction(self.save_action)
        self.action_group.addAction(self.run_action)

        for action in self.action_group.actions():
            action.setIcon(pango_get_icon(action.text()))

        self.addAction(self.action_group.actions()[0])
        self.addWidget(spacer_left)
        self.addActions(self.action_group.actions()[1:-1])
        self.addWidget(spacer_right)
        self.addAction(self.action_group.actions()[-1])


class PangoToolBarWidget(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIconSize(QSize(16, 16))
        
        spacer_left = QWidget()
        spacer_left.setFixedWidth(10)
        spacer_middle = QWidget()
        spacer_middle.setFixedWidth(50)
        spacer_right = QWidget()
        spacer_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Label Related
        self.color_display = QLabel()
        self.color_display.setFixedSize(QSize(50, 20))
        self.label_select = self.LabelSelect(self.color_display)
        self.label_select.lineEdit().returnPressed.connect(self.add_label)

        self.add_action = QAction("Add")
        self.add_action.triggered.connect(self.add_label)
        icon = pango_get_icon("add")
        self.add_action.setIcon(icon)

        self.del_action = QAction("Delete")
        self.del_action.triggered.connect(self.del_label)
        icon = pango_get_icon("del")
        self.del_action.setIcon(icon)

        self.color_action = QAction("Palette")
        self.color_action.triggered.connect(self.change_color)
        icon = pango_get_icon("palette")
        self.color_action.setIcon(icon)

        # Tool Related
        self.size_select = QSpinBox()
        self.size_select.setSuffix("px")
        self.size_select.setRange(1, 99)
        self.size_select.setSingleStep(5)
        self.size_select.setValue(10)

        self.pan_action = QAction("Pan")
        self.lasso_action = QAction("Lasso")
        self.path_action = QAction("Path")
        self.filled_path_action = QAction("Filled Path")
        self.rect_action = QAction("Rect")
        self.poly_action = QAction("Poly")

        self.action_group = QActionGroup(self)
        self.action_group.setExclusive(True)
        self.action_group.triggered.connect(self.toggle_size_select)

        self.action_group.addAction(self.pan_action)
        self.action_group.addAction(self.lasso_action)
        self.action_group.addAction(self.path_action)
        self.action_group.addAction(self.filled_path_action)
        self.action_group.addAction(self.rect_action)
        self.action_group.addAction(self.poly_action)

        for action in self.action_group.actions():
            icon = pango_get_icon(action.text())
            action.setIcon(icon)
            action.setCheckable(True)

        # Other
        font = QFont("Arial", 10)
        self.info_display = QLabel()
        self.info_display.setFixedWidth(100)
        self.info_display.setFont(font)

        self.coord_display = QLabel()
        self.coord_display.setFixedWidth(40)
        self.coord_display.setFont(font)

        # Layouts
        self.addWidget(spacer_left)
        self.addWidget(self.color_display)
        self.addWidget(self.label_select)
        self.addAction(self.add_action)
        self.addAction(self.del_action)
        self.addAction(self.color_action)

        self.addWidget(spacer_middle)
        self.addActions(self.action_group.actions())
        self.addWidget(self.size_select)

        self.addWidget(spacer_right)
        self.addWidget(self.info_display)
        self.addWidget(self.coord_display)

        self.size_select.setEnabled(False)
        self.label_select.setEnabled(False)
        self.action_group.setEnabled(False)
        self.color_action.setEnabled(False)

    def change_color(self):
        dialog = QColorDialog()
        dialog.setOption(QColorDialog.ShowAlphaChannel, False)
        row = self.label_select.currentIndex()
        color = dialog.getColor()

        label_item = self.label_select.model().item(row, 0)
        decoration = (label_item.decoration()[0], color)
        label_item.set_decoration(decoration)

        for n in range(0, label_item.rowCount()):
            child = label_item.child(n, 0)
            decoration = (child.decoration()[0], color)
            child.set_decoration(decoration)

        # Refresh label (for scene reticle etc.)
        self.label_select.setCurrentIndex(0)
        self.label_select.setCurrentIndex(row)

    def add_label(self):
        if not self.label_select.isEnabled():
            self.label_select.setEnabled(True)
            self.action_group.setEnabled(True)
            self.color_action.setEnabled(True)

        item = PangoLabelItem()

        root = self.label_select.model().invisibleRootItem()
        root.appendRow(item)

        item.set_decoration()
        item.set_name("Empty Label")

        self.label_select.setCurrentIndex(self.label_select.model().rowCount()-1)
        self.label_select.lineEdit().selectAll()

    def del_label(self):
        row = self.label_select.currentIndex()
        self.label_select.model().removeRow(row)

        if self.label_select.model().rowCount() == 0:
            self.label_select.setEnabled(False)
            self.action_group.setEnabled(False)
            self.color_action.setEnabled(False)

    def toggle_size_select(self, action):
        if action.text() == "Path" or action.text() == "Filled Path":
            self.size_select.setEnabled(True)
        else:
            self.size_select.setEnabled(False)

    def change_tool(self, text):
        for action in self.action_group.actions():
            if action.text() == text:
                action.setChecked(True)
                return

    class LabelSelect(QComboBox):
        def __init__(self, color_display, parent=None):
            super().__init__(parent)
            self.color_display = color_display
            self.setFixedWidth(150)
            self.setEditable(True)
            self.setEnabled(False)

            self.editTextChanged.connect(self.edit_text_changed)

        def paintEvent(self, event):
            super().paintEvent(event)
            item = self.model().item(self.currentIndex())
            if item is not None:
                _, color = item.decoration()
                if color is not None:
                    self.color_display.setStyleSheet(
                        "QLabel { background-color : "+color.name()+"}")

        def edit_text_changed(self, text):
            row = self.currentIndex()
            self.setItemData(row, text, Qt.DisplayRole)

class PangoStatusBarWidget(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(30)

        self.addPermanentWidget(self.coord_display)
