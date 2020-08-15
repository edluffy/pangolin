from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainterPath
from PyQt5.QtWidgets import (QDockWidget, QFileDialog, QHBoxLayout, QLineEdit,
                             QListView, QPushButton, QTreeView,
                             QVBoxLayout, QWidget)

PALETTE = [QColor('#e6194b'), QColor('#3cb44b'), QColor('#ffe119'),
           QColor('#4363d8'), QColor('#f58231'), QColor('#911eb4'),
           QColor('#46f0f0'), QColor('#f032e6'), QColor('#bcf60c'),
           QColor('#fabebe'), QColor('#008080'), QColor('#e6beff'),
           QColor('#9a6324'), QColor('#fffac8'), QColor('#800000'),
           QColor('#aaffc3'), QColor('#808000'), QColor('#ffd8b1'),
           QColor('#000075'), QColor('#808080')]


class PangoDockWidget(QDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)

        self.setWindowTitle(title)
        self.setFloating(True)

        self.bg = QWidget()
        self.setWidget(self.bg)

class PangoLabelWidget(PangoDockWidget):
    def __init__(self, selection, title, parent=None):
        super().__init__(title, parent)

        # Model and Views
        self.selection = selection
        self.model = selection.model()
        self.view = QListView()
        self.view.setModel(self.model)
        self.view.setSelectionModel(self.selection)

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
        name = self.line_edit.text()
        if name != '':
            color = QtGui.QColor(PALETTE[(self.model.rowCount()+1)%len(PALETTE)])
            self.model._layers.append([color, name, True, QPainterPath()])
            self.model.layoutChanged.emit()
        self.line_edit.clear()

    def delete(self):
        idxs = self.view.selectedIndexes()
        if idxs:
            if idxs[0].row() < len(self.model._layers):
                del self.model._layers[idxs[0].row()]
                self.model.layoutChanged.emit()
            else:
                self.view.clearSelection()

class PangoFileWidget(PangoDockWidget):
    def __init__(self, model, title, parent=None):
        super().__init__(title, parent)

        # Model and Views
        self.model = model
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
