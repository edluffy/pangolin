from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDockWidget, QHBoxLayout, QLineEdit, QPushButton,
                             QTreeView, QVBoxLayout, QWidget, QListView, QFileDialog)

from models.node import PALETTE


class PangoDockWidget(QDockWidget):
    def __init__(self, model, title, parent=None):
        super().__init__(title, parent)

        self.setWindowTitle(title)
        self.model = model
        self.setFloating(True)

        self.bg = QWidget()
        self.setWidget(self.bg)

class PangoLabelWidget(PangoDockWidget):
    def __init__(self, model, title, parent=None):
        super().__init__(model, title, parent)

        # Model and Views
        self.view = QTreeView()
        self.view.setModel(self.model)
        for i in range(0, 2):
            self.view.resizeColumnToContents(i)

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
        text = self.line_edit.text()
        if not text == '':
            color = QtGui.QColor(PALETTE[(len(self.model.data)+1)%len(PALETTE)])
            self.model.data.append((text, color))
            self.model.layoutChanged.emit()
        self.line_edit.clear()

    def delete(self):
        idxs = self.view.selectedIndexes()
        if idxs:
            if idxs[0].row() < len(self.model.data):
                del self.model.data[idxs[0].row()]
                self.model.layoutChanged.emit()
            else:
                self.view.clearSelection()

class PangoFileWidget(PangoDockWidget):
    def __init__(self, model, title, parent=None):
        super().__init__(model, title, parent)

        # Model and Views
        self.view = QListView()
        self.view.setViewMode(QListView.IconMode)
        self.view.setIconSize(QtCore.QSize(150, 150))
        self.view.setModel(self.model)

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
        self.model.files.extend(paths)
        self.model.layoutChanged.emit()
