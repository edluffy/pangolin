from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (QAction, QActionGroup, QComboBox, QLabel,
                             QSizePolicy, QSpinBox, QStatusBar, QToolBar,
                             QWidget)


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
        
        # Widgets
        spacer_left = QWidget()
        spacer_left.setFixedWidth(10)
        spacer_right = QWidget()
        spacer_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.color_display = QLabel()
        self.color_display.setFixedWidth(50)
        self.color_display.setFixedSize(QSize(50, 20))

        self.label_view = QComboBox()
        self.label_view.setFixedWidth(150)
        self.label_view.setEditable(False)
        self.label_view.currentIndexChanged.connect(self.set_color)

        self.size_select = QSpinBox()
        self.size_select.setSuffix("px")
        self.size_select.setRange(0, 99)
        self.size_select.setSingleStep(5)
        self.size_select.setValue(10)

        self.coord_display = QLabel()
        self.coord_display.setFixedWidth(40)
        font = QFont("Arial", 10)
        self.coord_display.setFont(font)

        # Actions
        self.pan_action = QAction("Pan")
        self.select_action = QAction("Select")
        self.path_action = QAction("Path")
        self.filled_path_action = QAction("Filled Path")
        self.rect_action = QAction("Rect")
        self.poly_action = QAction("Poly")

        self.action_group = QActionGroup(self)
        self.action_group.setExclusive(True)

        self.action_group.addAction(self.pan_action)
        self.action_group.addAction(self.select_action)
        self.action_group.addAction(self.path_action)
        self.action_group.addAction(self.filled_path_action)
        self.action_group.addAction(self.rect_action)
        self.action_group.addAction(self.poly_action)

        # Layouts
        self.addWidget(spacer_left)
        self.addWidget(self.color_display)
        self.addWidget(self.label_view)
        self.addWidget(self.size_select)

        for action in self.action_group.actions():
            icon = self.get_icon(action.text(), QColor("grey"))
            action.setIcon(icon)
            action.setCheckable(True)
        self.addActions(self.action_group.actions())

        self.addWidget(spacer_right)
        self.addWidget(self.coord_display)


    def reset_tool(self):
        self.select_action.setChecked(True)
        self.action_group.triggered.emit(self.select_action)

    def set_color(self, idx):
        color = self.label_view.itemData(idx, Qt.DecorationRole)
        if color is not None:
            self.color_display.setStyleSheet(
                "QLabel { background-color : "+color.name()+"}")

    def update_coords(self, scene_pos):
        coords = "x: "+str(scene_pos.x())+"\ny: "+str(scene_pos.y())
        self.coord_display.setText(coords)

class PangoStatusBarWidget(PangoBarMixin, QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(30)

        self.addPermanentWidget(self.coord_display)
