from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QHBoxLayout, QLineEdit, QListView, QPushButton,
                             QVBoxLayout)

from widgets.utils import PangoDockWidget, PangoPalette

class PangoLabelWidget(PangoDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)

        # Model and Views
        self.model = LabelModel()
        self.s_model = QtCore.QItemSelectionModel(self.model)
        
        self.view = QListView()
        self.view.setModel(self.model)
        self.view.setSelectionModel(self.s_model)

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
    
    def add(self):
        end = self.model.rowCount()+1
        idx = self.model.index(end)
        color = QtGui.QColor(PangoPalette[(end)%len(PangoPalette)])
        name = self.line_edit.text()

        self.model.insertRows(end, 1)
        self.model.setData(idx, color, Qt.DecorationRole)

        if name != '':
            self.model.setData(idx, name, Qt.DisplayRole)
            self.line_edit.clear()

    def delete(self):
        idxs = self.view.selectedIndexes()
        if idxs:
            if idxs[0].row() < len(self.model._layers):
                del self.model._layers[idxs[0].row()]
                self.model.layoutChanged.emit()
            else:
                self.view.clearSelection()

class LabelModel(QtCore.QAbstractListModel):
    def __init__(self, layers=None):
        super().__init__()
        self._layers = layers or []
        # Layer  = [color, name, visible, [paths]]

    def data(self, idx, role):
        if role == Qt.DecorationRole:
            color = self._layers[idx.row()][0]
            return color
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            name = self._layers[idx.row()][1]
            return name
        elif role == Qt.CheckStateRole:
            visible = self._layers[idx.row()][2]
            return Qt.Checked if visible else Qt.Unchecked
        elif role == Qt.UserRole:
            paths = self._layers[idx.row()][3]
            return paths

    def setData(self, idx, value, role):
        if self._layers == []:
            return True

        if role == Qt.DecorationRole:
            self._layers[idx.row()][0] = value
            self.dataChanged.emit(idx, idx)
            return True
        elif role == Qt.DisplayRole:
            self._layers[idx.row()][1] = value
            self.dataChanged.emit(idx, idx)
            return True
        elif role == Qt.EditRole:
            self._layers[idx.row()][1] = value
            self.dataChanged.emit(idx, idx)
            return True
        elif role == Qt.CheckStateRole:
            if value == Qt.Checked:
                self._layers[idx.row()][2] = True
            else:
                self._layers[idx.row()][2] = False
            self.dataChanged.emit(idx, idx)
            return True
        elif role == Qt.UserRole:
            paths = self._layers[idx.row()][3]
            paths.append(value)
            self.dataChanged.emit(idx, idx)
            return True
        return False

    def insertRows(self, pos, rows, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, pos, pos+rows-1)
        for _ in range(rows):
            self._layers.insert(pos, [QColor("grey"), "Empty Label", True, []])
        self.endInsertRows()
        return True

    def removeRows(self, pos, rows, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, pos, pos+rows-1)
        for _ in range(rows):
            del self._layers[pos]
        self.endRemoveRows()
        return True

    def rowCount(self, idx=None):
        return len(self._layers) 

    def flags(self, idx):
        return (Qt.ItemIsEnabled | Qt.ItemIsSelectable |
                Qt.ItemIsEditable | Qt.ItemIsUserCheckable)

