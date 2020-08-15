
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import (QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap,
                         QPolygonF, QStandardItem)
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QColorDialog,
                             QGraphicsItem, QGraphicsItemGroup,
                             QGraphicsPathItem, QGraphicsPixmapItem,
                             QGraphicsPolygonItem, QGraphicsRectItem,
                             QHBoxLayout, QLineEdit, QMessageBox, QPushButton,
                             QStyle, QTreeView, QVBoxLayout)


class LayerModel(QtCore.QAbstractListModel):
    def __init__(self, layers):
        super().__init__()
        self._layers = layers or [[]]


    def data(self, idx, role):
        if role == Qt.DecorationRole:
            color = self._layers[idx.row()][0]
            return color
        elif role == Qt.DisplayRole:
            name = self._layers[idx.row()][1]
            return name
        elif role == Qt.CheckStateRole:
            visible = self._layers[idx.row()][2]
            return visible
        elif role == Qt.UserRole:
            path = self._layers[idx.row()][3]
            return path

    def setData(self, idx, value, role):
        if role == Qt.DisplayRole:
            return True
        if role == Qt.UserRole:
            path = self._layers[idx.row()][3]
            path.addPath(value)
            self.dataChanged.emit(idx, idx, Qt.UserRole)
            return True
        return False

    def rowCount(self, idx=None):
        return len(self._layers) 

    def flags(self, idx):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
