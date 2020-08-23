from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QStandardItemModel, QStandardItem, QPen
from PyQt5.QtWidgets import (QHBoxLayout, QLineEdit, QListView, QPushButton,
                             QVBoxLayout, QTreeView, QGraphicsItemGroup, QGraphicsPathItem)

from widgets.utils import PangoDockWidget
from widgets.utils import PangoPalette

from item import PangoStandardItem

class PangoLabelWidget(PangoDockWidget):
    labelChanged = pyqtSignal(PangoStandardItem)
    def __init__(self, title, item_map, parent=None):
        super().__init__(title, parent)

        self.item_map = item_map

        # Model and Views
        self.model = QStandardItemModel()

        self.view = QTreeView()
        self.view.setModel(self.model)

        self.view.selectionModel().selectionChanged.connect(self.get_label)
        self.model.dataChanged.connect(self.data_changed)

        # Toolbars and menus

        # Widgets
        self.line_edit = QLineEdit()
        self.line_edit.returnPressed.connect(self.add)
        self.line_edit.setPlaceholderText("Enter a new label")

        self.delete_button = QPushButton("-")
        self.delete_button.pressed.connect(self.delete)
        self.add_button = QPushButton("+")
        self.add_button.pressed.connect(self.add)

        # Layouts
        self.layout = QVBoxLayout(self.bg)
        self.button_layout = QHBoxLayout()

        self.layout.addWidget(self.line_edit)
        self.layout.addWidget(self.view)
        self.layout.addLayout(self.button_layout)

        self.button_layout.addWidget(self.delete_button)
        self.button_layout.addWidget(self.add_button)

    def data_changed(self, top_left, bottom_right, role):
        std_item = self.model.itemFromIndex(top_left)

        try:
            gfx_item = self.item_map[QtCore.QPersistentModelIndex(top_left)]
        except KeyError:
            return

        check_state = std_item.data(Qt.CheckStateRole)
        visible = True if check_state == Qt.Checked else False
        gfx_item.setVisible(visible)

    def get_label(self, selected, deselected):
        if selected.indexes() != []:
            s_idx = selected.indexes()[0]

            parent_idx = s_idx.parent()
            while parent_idx.isValid():
                s_idx = parent_idx
                parent_idx = s_idx.parent()

            label_item = self.model.itemFromIndex(s_idx)
            self.labelChanged.emit(label_item)

    def add(self):
        root = self.model.invisibleRootItem()

        std_item = PangoStandardItem("Group", root)
        gfx_item = QGraphicsItemGroup()
        self.item_map[std_item.map_index()] = gfx_item

        text = self.line_edit.text()
        std_item.setText(text)
        self.line_edit.clear()

    def delete(self):
        pass
        #idxs = self.view.selectedIndexes()
        #if idxs:
        #    if idxs[0].row() < len(self.model._layers):
        #        del self.model._layers[idxs[0].row()]
        #        self.model.layoutChanged.emit()
        #    else:
        #        self.view.clearSelection()

