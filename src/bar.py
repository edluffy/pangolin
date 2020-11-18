from PyQt5.QtCore import QModelIndex, QPoint, QSize, Qt, pyqtSignal, QSortFilterProxyModel
from PyQt5.QtGui import QColor, QFont, QIcon
from PyQt5.QtWidgets import (QAction, QActionGroup, QColorDialog, QComboBox,
                             QLabel, QSizePolicy, QSpinBox, QStatusBar, QStyle, QStyleOptionComboBox, QToolBar, QWidget)
from graphics import PangoGraphicsScene

from item import PangoLabelItem
from utils import pango_get_icon, pango_get_palette


class PangoMenuBarWidget(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setIconSize(QSize(16, 16))
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # Widgets
        spacer_left = QWidget()
        spacer_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer_right = QWidget()
        spacer_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Actions
        self.action_group = QActionGroup(self)

        self.prefs_action = QAction("Prefs")
        self.prefs_action.setIcon(pango_get_icon("prefs"))
        self.action_group.addAction(self.prefs_action)

        self.open_images_action = QAction("Open Images")
        self.open_images_action.setIcon(pango_get_icon("open"))
        self.action_group.addAction(self.open_images_action)

        self.import_labels_action = QAction("Import Labels")
        self.import_labels_action.setIcon(pango_get_icon("import"))
        self.action_group.addAction(self.import_labels_action)

        self.save_action = QAction("Save Project")
        self.save_action.setIcon(pango_get_icon("save"))
        self.action_group.addAction(self.save_action)

        self.load_action = QAction("Load Project")
        self.load_action.setIcon(pango_get_icon("load"))
        self.action_group.addAction(self.load_action)

        self.run_action = QAction("PyTorch")
        self.run_action.setIcon(pango_get_icon("fire"))
        self.action_group.addAction(self.run_action)

        self.addAction(self.action_group.actions()[0])
        #self.addWidget(spacer_left)
        self.addActions(self.action_group.actions()[1:-1])
        self.addWidget(spacer_right)
        self.addAction(self.action_group.actions()[-1])


class PangoToolBarWidget(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIconSize(QSize(16, 16))
        self.scene = None
        
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
        self.color_action.triggered.connect(self.set_color)
        icon = pango_get_icon("palette")
        self.color_action.setIcon(icon)

        # Tool Related
        self.size_select = QSpinBox()
        self.size_select.valueChanged.connect(self.set_tool_size)


        self.size_select.setSuffix("px")
        self.size_select.setRange(1, 99)
        self.size_select.setSingleStep(5)
        self.size_select.setValue(10)

        self.pan_action = QAction("Pan")
        self.lasso_action = QAction("Lasso")
        self.path_action = QAction("Path")
        self.bbox_action = QAction("Bbox")
        self.poly_action = QAction("Poly")

        self.action_group = QActionGroup(self)
        self.action_group.setExclusive(True)
        self.action_group.triggered.connect(self.set_tool)

        self.action_group.addAction(self.pan_action)
        self.action_group.addAction(self.lasso_action)
        self.action_group.addAction(self.bbox_action)
        self.action_group.addAction(self.poly_action)
        self.action_group.addAction(self.path_action)

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
        self.add_action.setEnabled(False)
        self.del_action.setEnabled(False)
        self.action_group.setEnabled(False)
        self.color_action.setEnabled(False)


    def set_color(self):
        dialog = QColorDialog()
        dialog.setOption(QColorDialog.ShowAlphaChannel, False)
        row = self.label_select.currentIndex()
        color = dialog.getColor()
        if color == QColor():
            return
        name = self.label_select.model().item(row, 0).name

        for row in range(0, self.label_select.count()):
            label = self.label_select.model().item(row, 0)
            if label.name == name:
                label.color = color
                label.set_icon()
                for n in range(0, label.rowCount()):
                    child = label.child(n, 0)
                    child.set_icon()

        # Refresh label (for scene reticle etc.)
        self.label_select.setCurrentIndex(0)
        self.label_select.setCurrentIndex(row)

        self.label_select.color_display.update()

    def filter_label_select(self, new_fpath):
        for row in range(0, self.label_select.count()):
            item = self.label_select.model().item(row, 0)
            self.label_select.view().setRowHidden(row, item.fpath!=self.scene.fpath)
        self.label_select.model().sort(0)

        # Select first valid label
        for row in range(0, self.label_select.count()):
            if self.label_select.view().isRowHidden(row) is False:
                self.label_select.setCurrentIndex(row)

    def add_label(self):
        if not self.label_select.isEnabled():
            self.label_select.setEnabled(True)
            self.action_group.setEnabled(True)
            self.color_action.setEnabled(True)

        item = PangoLabelItem()
        root = self.label_select.model().invisibleRootItem()
        root.appendRow(item)
        item.fpath = self.scene.fpath
        item.name = "Empty Label "+str(item.unique_row())
        item.visible = True
        item.color = pango_get_palette(item.unique_row()-1)
        item.set_icon()

        bottom_row = self.label_select.model().rowCount()-1
        self.label_select.setCurrentIndex(bottom_row)
        if bottom_row == 0:
            self.label_select.currentIndexChanged.emit(self.label_select.currentIndex())

    def del_label(self):
        self.scene.clear_changes.emit()
        if self.scene.stack.count() == 0:
            row = self.label_select.currentIndex()
            name = self.label_select.model().item(row, 0).name

            for i in range(0, self.label_select.count()):
                label = self.label_select.model().item(i, 0)
                if label.name == name:
                    for j in range(0, label.rowCount()):
                        self.label_select.model().removeRow(j, label.index())
                    self.label_select.model().removeRow(i)

            if self.label_select.model().rowCount() == 0:
                self.label_select.setEnabled(False)
                self.action_group.setEnabled(False)
                self.color_action.setEnabled(False)

    def set_tool(self, action):
        if self.scene is None:
            return

        self.scene.tool = action.text()
        self.scene.reset_com()
        self.scene.reticle.setVisible(self.scene.tool == "Path")
        self.scene.views()[0].set_cursor(self.scene.tool)

        if action.text() == "Path" or action.text() == "Filled Path":
            self.size_select.setEnabled(True)
        else:
            self.size_select.setEnabled(False)

    def reset_tool(self):
        self.lasso_action.setChecked(True)
        self.set_tool(self.lasso_action)

    def set_tool_size(self, size):
        if self.scene is None:
            return

        self.scene.tool_size = size
        self.scene.reset_com()

        view = self.scene.views()[0]
        x = self.size_select.geometry().center().x()
        y = view.rect().top() + size/2
        self.scene.reticle.setRect(-size/2, -size/2, size, size)
        self.scene.reticle.setPos(view.mapToScene(QPoint(x, y)))

    def set_scene(self, scene):
        if self.scene is not None:
            self.scene.clear_tool.disconnect(self.reset_tool)

        self.scene = scene
        self.scene.clear_tool.connect(self.reset_tool)
        self.reset_tool()

        if not self.add_action.isEnabled() or self.del_action.isEnabled():
            self.add_action.setEnabled(True)
            self.del_action.setEnabled(True)

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
                if item.color is not None:
                    self.color_display.setStyleSheet(
                        "QLabel { background-color : "+item.color.name()+"}")

        def edit_text_changed(self, text):
            row = self.currentIndex()
            self.setItemData(row, text, Qt.DisplayRole)

class PangoStatusBarWidget(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(30)

        self.addPermanentWidget(self.coord_display)
