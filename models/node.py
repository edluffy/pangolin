
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

PALETTE = [QColor('#e6194b'), QColor('#3cb44b'), QColor('#ffe119'),
           QColor('#4363d8'), QColor('#f58231'), QColor('#911eb4'),
           QColor('#46f0f0'), QColor('#f032e6'), QColor('#bcf60c'),
           QColor('#fabebe'), QColor('#008080'), QColor('#e6beff'),
           QColor('#9a6324'), QColor('#fffac8'), QColor('#800000'),
           QColor('#aaffc3'), QColor('#808000'), QColor('#ffd8b1'),
           QColor('#000075'), QColor('#808080')]


class NodeModel(QtCore.QAbstractItemModel):
    def __init__(self, root, parent=None):
        super().__init__(parent)
        self._root_node = root

    def data(self, idx, role=Qt.DisplayRole):
        node = self.node_from_index(idx)
        if (role == Qt.DisplayRole or role == Qt.EditRole) and idx.column() == 0:
            return node.name()

        elif role == Qt.DecorationRole and idx.column() == 0:
            return node.icon()
        elif role == Qt.DecorationRole and idx.column() == 1:
            return node.color()

        elif role == Qt.CheckStateRole and idx.column() == 2:
            return Qt.Checked if node.isVisible() else Qt.Unchecked
        elif role == Qt.DisplayRole and idx.column() == 2:
            return str(node.x()) 

    def setData(self, idx, value, role=Qt.DisplayRole):
        node = self.node_from_index(idx)
        if role == Qt.EditRole:
            node._name = value
            node.set_name(value)
            self.dataChanged.emit(idx, idx)
            return True
        elif role == Qt.CheckStateRole:
            state = True if value == Qt.Checked else False
            node.setVisible(state)
            for child_node in node.children():
                child_node.setVisible(state)
            self.dataChanged.emit(idx, idx)
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
        #if node.type_info()=="Group" and idx.column()==0:
        return (Qt.ItemIsEnabled | Qt.ItemIsSelectable
                | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)
        #else:
        #    return (Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)


class Node(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCacheMode(QGraphicsItem.ItemCoordinateCache)

        self._name = ""
        self._color = None
        self._icon = None
        self._children = []
        
        if parent is not None:
            self._parent = parent
            parent.add_child(self)

            if parent._color is not None:
                self._color = parent._color

            siblings = self.siblings(same_type=True)
            self._name = self.type_info()+" "+str(siblings.index(self)) 

    def name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    def color(self):
        if self._color is None:
            return self._parent._color
        else:
            return self._color

    def set_color(self, color):
        self._color = color

    def icon(self):
        return self._icon

    def child(self, row):
        return self._children[row]

    def children(self):
            return self._children

    def add_child(self, child, pos=QtCore.QPointF(0, 0)):
        self._children.append(child)
        if self.scene() is not None:
            self.scene().addItem(child)
            child.setPos(pos)

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

class GroupNode(Node):
    def __init__(self, name, color, parent=None):
        super().__init__(parent)

        self._name = name
        self._color = color

    def type_info(self):
        return "Group"

class PixmapNode(Node):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._icon = QApplication.style().standardIcon(QStyle.SP_ComputerIcon)

    def type_info(self):
        return "Pixmap"


class RectangleNode(Node):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._icon = QApplication.style().standardIcon(QStyle.SP_DriveDVDIcon)

    def type_info(self):
        return "Rectangle"


class PolygonNode(QGraphicsPolygonItem, Node):
    def __init__(self, polygon, parent=None):
        super().__init__(parent)
        self._icon = QApplication.style().standardIcon(QStyle.SP_TrashIcon)

        self.setAcceptHoverEvents(True)
        self.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        self.setFlags(QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)

        self._dots = []

    def type_info(self):
        return "Polygon"


class DotNode(QGraphicsPathItem, Node):
    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.setZValue(-1)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        self.setFlags(QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)

        self._index = index

        self._circle = QPainterPath()
        self._circle.addEllipse(QtCore.QRectF(-4, -4, 8, 8))
        self._square = QPainterPath()
        self._square.addRect(QRectF(-5, -5, 10, 10))

        self.setPath(self._circle)
        self.setBrush(QColor(self.color()))
        self.setPen(QPen(QtCore.Qt.NoPen))

    def hoverEnterEvent(self, event):
        self.setBrush(QColor("black"))

    def hoverLeaveEvent(self, event):
        self.setBrush(QColor(self.color()))

    def mouseReleaseEvent(self, event):
        self.setSelected(False)

    #def itemChange(self, change, value):
    #    if change == QtWidgets.QGraphicsItem.ItemPositionChange and self.isEnabled():
    #        self.m_annotation_item.movePoint(self.m_index, value)
    #    return super(GripItem, self).itemChange(change, value)
