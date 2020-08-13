
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import (QColor, QIcon, QPainter, QPixmap, QPolygonF,
                         QStandardItem)
from PyQt5.QtWidgets import (QApplication, QColorDialog, QHBoxLayout,
                             QLineEdit, QMessageBox, QPushButton, QStyle,
                             QTreeView, QVBoxLayout, QAbstractItemView)


PALETTE = [QColor('#e6194b'), QColor('#3cb44b'), QColor('#ffe119'),
           QColor('#4363d8'), QColor('#f58231'), QColor('#911eb4'),
           QColor('#46f0f0'), QColor('#f032e6'), QColor('#bcf60c'),
           QColor('#fabebe'), QColor('#008080'), QColor('#e6beff'),
           QColor('#9a6324'), QColor('#fffac8'), QColor('#800000'),
           QColor('#aaffc3'), QColor('#808000'), QColor('#ffd8b1'),
           QColor('#000075'), QColor('#808080')]


class NodeModel(QtCore.QAbstractItemModel):
    def __init__(self, root=None):
        super(NodeModel, self).__init__()
        self._root_node = root

    def data(self, idx, role):
        node = self.node_from_index(idx)
        if (role == Qt.DisplayRole or role == Qt.EditRole) and idx.column() == 0:
            if node.type_info() == "Label":
                return node.name()
            else:
                n = node.siblings(same_type=True).index(node)
                return node.type_info() + str(n)
        elif role == Qt.DecorationRole and idx.column() == 0:
            return node.icon()

        elif role == Qt.DecorationRole and idx.column() == 1:
            return node.color()

        elif role == Qt.CheckStateRole and idx.column() == 2:
            return Qt.Checked if node.visible() else Qt.Unchecked

    def setData(self, idx, value, role):
        node = self.node_from_index(idx)
        if role == Qt.EditRole:
            node._name = value
            node.set_name(value)
            return True
        elif role == Qt.CheckStateRole:
            state = True if value == Qt.Checked else False
            node.set_visible(state)
            for child_node in node.children():
                child_node.set_visible(state)
            self.layoutChanged.emit()
            return True
        return False

    def headerData(self, section, orient, role):
        if role == Qt.DisplayRole:
            pass

    def rowCount(self, parent):
        parent_node = self.node_from_index(parent)
        if parent_node is None:
            return 0
        return len(parent_node)

    def columnCount(self, parent):
        return 3

    def parent(self, idx):
        node = self.node_from_index(idx)
        parent_node = node.parent()

        if parent_node == self._root_node:
            return QtCore.QModelIndex()
        else:
            return self.createIndex(parent_node.row(), 0, parent_node)

    """ Returns QModelIndex that corresponds to given row, col and parent """
    def index(self, row, col, parent):
        node = self.node_from_index(parent)
        return self.createIndex(row, col, node.child(row))

    def node_from_index(self, idx):
        return idx.internalPointer() if idx.isValid() else self._root_node

    def flags(self, idx):
        node = self.node_from_index(idx)
        if node.type_info() == "LabelNode":
            return (Qt.ItemIsEnabled | Qt.ItemIsSelectable
                    | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)
        else:
            return (Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)


class Node(object):
    def __init__(self, item=None, parent=None, color=None):

        self._item = item
        self._color = color
        self._visible = True
        self._icon = None
        self._children = []
        
        if parent is not None:
            self._parent = parent
            parent.add_child(self)
            if parent._color is not None:
                self._color = parent._color

    def color(self):
        return self._color

    def set_color(self, color):
        self._color = color

    def icon(self):
        return self._icon

    def visible(self):
        return self._visible

    def set_visible(self, state):
        self._visible = state

    def child(self, row):
        return self._children[row]

    def children(self):
            return self._children

    def add_child(self, child):
        self._children.append(child)

    def siblings(self, same_type=False):
        if same_type == False:
            return self.parent().children()
        else:
            matching_siblings = []
            for sibling in self.parent().children():
                if sibling.type_info() == self.type_info():
                    matching_siblings.append(sibling)
            return matching_siblings

    def parent(self):
        return self._parent

    def row(self):
        if self._parent is not None:
            return self._parent._children.index(self)

    def __len__(self):
        return len(self._children)

    def type_info(self):
        return "Node"

class LabelNode(Node):
    def __init__(self, name, parent=None, color=None):
        super(LabelNode, self).__init__(name, parent, color)
        self._name = name
        self._item = None

    def name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    def type_info(self):
        return "Label"

class PolygonNode(Node):
    def __init__(self, item, parent=None):
        super(PolygonNode, self).__init__(item, parent)
        self._icon = QApplication.style().standardIcon(QStyle.SP_TrashIcon)

    def type_info(self):
        return "Polygon"

class PixmapNode(Node):
    def __init__(self, item, parent=None):
        super(PixmapNode, self).__init__(item, parent)
        self._icon = QApplication.style().standardIcon(QStyle.SP_ComputerIcon)

    def type_info(self):
        return "Pixmap"

class RectangleNode(Node):
    def __init__(self, item, parent=None):
        super(RectangleNode, self).__init__(item, parent)
        self._icon = QApplication.style().standardIcon(QStyle.SP_DriveDVDIcon)

    def type_info(self):
        return "Rectangle"
