from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter, QPixmap, QPolygonF, QPainterPath, QPen
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QGraphicsScene,
                             QGraphicsView, QLabel, QStackedLayout, QStyle,
                             QTabWidget, QGraphicsPolygonItem)

from widgets.bar import PangoToolBarWidget

class PangoCanvasWidget(QTabWidget):
    def __init__(self, selection, parent=None):
        super().__init__(parent)

        # Model and Views
        self.selection = selection
        self.model = selection.model()
        self.view = CanvasView()
        self.view.setModel(self.model)
        self.view.setSelectionModel(self.selection)

        # Toolbars and menus
        self.tool_bar = PangoToolBarWidget()
        self.tool_bar.action_group.triggered.connect(self.view.change_tool)
        self.parentWidget().addToolBar(Qt.LeftToolBarArea, self.tool_bar)

        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)


        # Widgets
        example_label = QLabel("hey")
        example_label2 = QLabel("lol")

        # Layouts
        self.addTab(self.view, QApplication.style().standardIcon(
            QStyle.SP_ComputerIcon), "003.jpg")

        self.addTab(example_label, QApplication.style().standardIcon(
            QStyle.SP_FileDialogNewFolder), "001.jpg")

        self.addTab(example_label2, QApplication.style().standardIcon(
            QStyle.SP_ComputerIcon), "002.jpg")


class CanvasView(QAbstractItemView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tool = None

        self.s_idx = QtCore.QModelIndex()


    def selectionChanged(self, selected, deselected):
        if selected.indexes() != []:
            self.s_idx = selected.indexes()[0]

    def mousePressEvent(self, event):
        if self.tool == "Brush":
            self.sub_path = QPainterPath()
            self.sub_path.moveTo(event.pos())

    def mouseMoveEvent(self, event):
        if self.tool == "Brush" and self.sub_path is not None:
            #self.sub_path.lineTo(event.pos())
            self.sub_path.addEllipse(event.pos(), 10, 10)

            self.model().setData(self.s_idx, self.sub_path, Qt.UserRole)
            self.viewport().update()

    def mouseReleaseEvent(self, event):
        if self.tool == "Brush" and self.sub_path is not None:
            self.model().setData(self.s_idx, self.sub_path, Qt.UserRole)
            self.viewport().update()

            self.sub_path.closeSubpath()
            self.sub_path = None

   # def paintEvent(self, event):
   #     qp = QPainter(self.viewport())
   #     for row in range(0, self.model().rowCount()):
   #         idx = self.model().index(row)
   #
   #         path = self.model().data(idx, Qt.UserRole)
   #         color = self.model().data(idx, Qt.DecorationRole)
   #
   #         pen = QPen()
   #         pen.setWidth(10)
   #         pen.setColor(color)
   #
   #         qp.setPen(pen)
   #         qp.drawPath(path)

    def dataChanged(self, top_left, bottom_right, role):
        if role == Qt.DecorationRole:
            pass
        elif role == Qt.CheckStateRole:
            pass
        elif role == Qt.UserRole:
            path = self._layers[top_left.row()][3]
            color = self._layers[top_left.row()][0]

            qp = QPainter(self.viewport())
            pen = QPen()
            pen.setWidth(10)
            pen.setColor(color)

            qp.setPen(pen)
            qp.drawPath(path)
            self.viewport().update()
         


    def change_tool(self, action):
        self.tool = action.text()
