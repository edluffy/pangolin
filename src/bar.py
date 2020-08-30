from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (QAction, QActionGroup, QComboBox, QLabel,
                             QSizePolicy, QSpinBox, QStatusBar, QToolBar,
                             QWidget)

from item import PangoHybridItem

class PangoBarMixin(object):
    def get_icon(self, text, color):
        fn = ":/icons/"+text.lower().replace(" ", "_")+".png"
        px = QPixmap(fn)
        mask = px.createMaskFromColor(QColor('white'), Qt.MaskOutColor)
        px.fill(color)
        px.setMask(mask)

        return QIcon(px)


class PangoMenuBarWidget(PangoBarMixin, QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setIconSize(QtCore.QSize(24, 24))
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
            icon = self.get_icon(action.text(), QColor("grey"))
            action.setIcon(icon)

        self.addAction(self.action_group.actions()[0])
        self.addWidget(spacer_left)
        self.addActions(self.action_group.actions()[1:-1])
        self.addWidget(spacer_right)
        self.addAction(self.action_group.actions()[-1])


class PangoToolBarWidget(PangoBarMixin, QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIconSize(QtCore.QSize(16, 16))
        
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
        icon = self.get_icon("add", QColor("grey"))
        self.add_action.setIcon(icon)

        self.del_action = QAction("Delete")
        self.del_action.triggered.connect(self.del_label)
        icon = self.get_icon("del", QColor("grey"))
        self.del_action.setIcon(icon)

        # Tool Related
        self.size_select = self.SizeSelect()
        self.size_select.setSuffix("px")
        self.size_select.setRange(1, 99)
        self.size_select.setSingleStep(5)
        self.size_select.setValue(10)
        self.size_select.setEnabled(False)

        self.pan_action = QAction("Pan")
        self.select_action = QAction("Select")
        self.path_action = QAction("Path")
        self.filled_path_action = QAction("Filled Path")
        self.rect_action = QAction("Rect")
        self.poly_action = QAction("Poly")

        self.action_group = QActionGroup(self)
        self.action_group.setExclusive(True)
        self.action_group.triggered.connect(self.toggle_size_select)

        self.action_group.addAction(self.pan_action)
        self.action_group.addAction(self.select_action)
        self.action_group.addAction(self.path_action)
        self.action_group.addAction(self.filled_path_action)
        self.action_group.addAction(self.rect_action)
        self.action_group.addAction(self.poly_action)

        for action in self.action_group.actions():
            icon = self.get_icon(action.text(), QColor("grey"))
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

        self.addWidget(spacer_middle)
        self.addActions(self.action_group.actions())
        self.addWidget(self.size_select)

        self.addWidget(spacer_right)
        self.addWidget(self.info_display)
        self.addWidget(self.coord_display)

    def add_label(self):
        if not self.label_select.isEnabled():
            self.label_select.setEnabled(True)

        root = self.label_select.model().invisibleRootItem()
        item = PangoHybridItem("Label", root)
        item.setText("Empty Label")

        self.label_select.setCurrentIndex(self.label_select.model().rowCount()-1)
        self.label_select.lineEdit().selectAll()

    def del_label(self):
        row = self.label_select.currentIndex()
        self.label_select.model().removeRow(row)

        if self.label_select.model().rowCount() == 0:
            self.label_select.setEnabled(False)

    def toggle_size_select(self, action):
        if action.text() == "Path" or action.text() == "Filled Path":
            self.size_select.setEnabled(True)
        else:
            self.size_select.setEnabled(False)

    def reset_tool(self):
        self.select_action.setChecked(True)
        self.action_group.triggered.emit(self.select_action)

    def update_coords(self, scene_pos):
        coords = "x: "+str(scene_pos.x())+"\ny: "+str(scene_pos.y())
        self.coord_display.setText(coords)

    def update_info(self, text):
        if text is not "":
            info = "Drawing: "+text
        else:
            info = ""
        self.info_display.setText(info)

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
                color = item.data(Qt.DecorationRole)
                if color is not None:
                    self.color_display.setStyleSheet(
                        "QLabel { background-color : "+color.name()+"}")

        def edit_text_changed(self, text):
            row = self.currentIndex()
            self.setItemData(row, text, Qt.DisplayRole)

    class SizeSelect(QSpinBox):
        hover_change = pyqtSignal(bool, QtCore.QPoint)
        def __init__(self, parent=None):
            super().__init__(parent)

        def mousePressEvent(self, event):
            super().mousePressEvent(event)
            center = self.geometry().center()
            self.hover_change.emit(True, center)

        def leaveEvent(self, event):
            super().leaveEvent(event)
            self.hover_change.emit(False, QtCore.QPoint())


class PangoStatusBarWidget(PangoBarMixin, QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(30)

        self.addPermanentWidget(self.coord_display)
