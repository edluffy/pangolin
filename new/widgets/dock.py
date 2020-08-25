from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QStandardItem
from PyQt5.QtWidgets import (QDockWidget, QGraphicsItemGroup,
                             QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout,
                             QWidget, QFileSystemModel, QListView, QFileDialog, QFileIconProvider)

from item import PangoHybridItem

class PangoDockWidget(QDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)

        self.setWindowTitle(title)
        self.setFloating(True)

        self.bg = QWidget()
        self.setWidget(self.bg)

        self.setTitleBarWidget(QWidget())

class PangoLabelWidget(PangoDockWidget):
    def __init__(self, title, view, parent=None):
        super().__init__(title, parent)
        self.view = view

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
        root = self.view.model().invisibleRootItem()
        item = PangoHybridItem("Path", root)

        text = self.line_edit.text()
        if text:
            item.setData(text, Qt.DisplayRole)
        self.line_edit.clear()

    def delete(self):
        if self.view.selectedIndexes() != []:
            idx = self.view.selectedIndexes()[0]
            self.view.model().removeRow(idx.row())

class PangoFileWidget(PangoDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)

        self.file_model = QFileSystemModel()
        self.thumbnail_provider = ThumbnailProvider()
        self.file_model.setIconProvider(self.thumbnail_provider)

        self.file_view = QListView()
        self.file_view.setModel(self.file_model)
        #self.file_view.setViewMode(QListView.IconMode)
        self.file_view.setIconSize(QtCore.QSize(200, 200))

        # Widgets
        self.setWidget(self.file_view)

        # Layouts

    def open_images(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        dialog.exec()

        self.file_model.setRootPath(dialog.directory().absolutePath())
        self.file_view.setRootIndex(self.file_model.index(self.file_model.rootPath()))

class ThumbnailProvider(QFileIconProvider):
    def __init__(self):
        super().__init__()
        pass

    def icon(self, type: 'QFileIconProvider.IconType'):
        fn = type.filePath()

        if fn.endswith(".jpg"):
            a = QtGui.QPixmap(QtCore.QSize(100, 100))
            a.load(fn)
            return QtGui.QIcon(a)
        else:
            return super().icon(type)

