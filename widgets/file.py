import os.path
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter
from PyQt5.QtWidgets import QListView, QVBoxLayout, QPushButton, QFileDialog

from widgets.utils import PangoDockWidget

class PangoFileWidget(PangoDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)

        # Model and Views
        self.model = FileModel()
        self.s_model = QtCore.QItemSelectionModel(self.model)

        self.view = QListView()
        self.view.setModel(self.model)
        self.view.setSelectionModel(self.s_model)

        self.view.setViewMode(QListView.IconMode)
        self.view.setIconSize(QtCore.QSize(150, 150))

        # Toolbars and menus

        # Widgets
        self.import_button = QPushButton("Select Images")
        self.import_button.pressed.connect(self.import_)

        # Layouts
        self.layout = QVBoxLayout(self.bg)

        self.layout.addWidget(self.import_button)
        self.layout.addWidget(self.view)

    def import_(self):
        paths, _ = QFileDialog.getOpenFileNames(self,
            "Open image file(s)", "Images (*.png *.jpg)")

        for path in paths:
            end = self.model.rowCount()+1
            idx = self.model.index(end)

            self.model.insertRows(end, 1)
            self.model.setData(idx, path, Qt.ToolTipRole)

class FileModel(QtCore.QAbstractListModel):
    def __init__(self, files=None):
        super().__init__()
        self._files = files or []
        # Files = [fpath, saved, opened, [paths]]

    def data(self, idx, role):
        if role == Qt.DisplayRole:
            title = os.path.basename(self._files[idx.row()][0]) 
            saved = self._files[idx.row()][1]
            opened = self._files[idx.row()][2]

            title += " (unsaved)" if not saved else ""
            title += " (opened)" if opened else ""
            return title
        elif role == Qt.DecorationRole:
            icon = QIcon(self._files[idx.row()][0])
            return icon
        elif role == Qt.ToolTipRole:
            return self._files[idx.row()][0]
        elif role == Qt.UserRole:
            saved = self._files[idx.row()][1]
            return saved
        elif role == Qt.UserRole+1:
            opened = self._files[idx.row()][2]
            return opened

    def setData(self, idx, value, role):
        if role == Qt.DecorationRole:
            self._files[idx.row()][3] = value
            self.dataChanged.emit(idx, idx)
        elif role == Qt.ToolTipRole:
            self._files[idx.row()][0] = value
            self.dataChanged.emit(idx, idx)
        elif role == Qt.UserRole:
            self._files[idx.row()][1] = value
            self.dataChanged.emit(idx, idx)
        elif role == Qt.UserRole+1:
            self._files[idx.row()][2] = value
            self.dataChanged.emit(idx, idx)


    def insertRows(self, pos, rows, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, pos, pos+rows-1)
        for _ in range(rows):
            self._files.insert(pos, [None, True, False, QPixmap()])
        self.endInsertRows()
        return True


    def rowCount(self, idx=None):
        return len(self._files)
