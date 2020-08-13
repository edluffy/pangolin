import os.path

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QVBoxLayout, QListView, QFileDialog, QPushButton

class FileModel(QtCore.QAbstractListModel):
    def __init__(self, files, *args, **kwargs):
        super(FileModel, self).__init__(*args, **kwargs)

        self.files = files or []
        self.pxs = []
        for f in files:
            self.pxs.append(QIcon(f))

    def data(self, index, role):
        if role == Qt.DisplayRole:
            fn = os.path.basename(self.files[index.row()]) 
            return fn
        if role == Qt.DecorationRole:
            #px = QIcon(self.files[index.row()])
            return self.pxs[index.row()]
        if role == Qt.ToolTipRole:
            return self.files[index.row()]

    def rowCount(self, index):
        return len(self.files)

