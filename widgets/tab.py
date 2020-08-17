from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter, QPixmap, QPolygonF, QPainterPath, QPen
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QGraphicsScene,
                             QGraphicsView, QLabel, QStackedLayout, QStyle,
                             QTabWidget, QGraphicsPolygonItem)

from widgets.bar import PangoToolBarWidget

class PangoCanvasWidget(QTabWidget):
    def __init__(self, label_selection, file_selection, parent=None):
        super().__init__(parent)
        self.label_selection = label_selection
        self.file_selection = file_selection

        # Model and Views

        # Toolbars and menus
        self.tool_bar = PangoToolBarWidget()
        #self.tool_bar.action_group.triggered.connect(self.view.change_tool)
        #self.parentWidget().addToolBar(Qt.LeftToolBarArea, self.tool_bar)

        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)


        # Widgets
        example_label = QLabel("hey")
        example_label2 = QLabel("lol")

        # Layouts
        #self.addTab(self.view, QApplication.style().standardIcon(
        #    QStyle.SP_ComputerIcon), "003.jpg")

        self.addTab(example_label, QApplication.style().standardIcon(
            QStyle.SP_FileDialogNewFolder), "001.jpg")

        self.addTab(example_label2, QApplication.style().standardIcon(
            QStyle.SP_ComputerIcon), "002.jpg")
        

    def new_tab(self, idx):
        model = self.file_selection.model()
        fn = model.data(idx, Qt.DisplayRole)
        path = model.data(idx, Qt.ToolTipRole)

        self.view = CanvasView(path)
        self.view.setModel(self.label_selection.model())
        self.view.setSelectionModel(self.label_selection)

        self.addTab(self.view, QApplication.style().standardIcon(
            QStyle.SP_ComputerIcon), fn)


class CanvasView(QAbstractItemView):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.s_idx = QtCore.QModelIndex()
        self.px_img = QPixmap(path)
        self.px_stack = QPixmap(self.px_img.size())

        self.sub_path = None
        self.tool = None

        self.pen = QPen()
        self.pen.setWidth(10)
        self.pen.setCapStyle(Qt.RoundCap)

    def mousePressEvent(self, event):
        if self.tool == "Brush":
            self.sub_path = QPainterPath()
            self.sub_path.moveTo(event.pos())

    def mouseMoveEvent(self, event):
        if self.tool == "Brush" and self.sub_path is not None:
            self.sub_path.lineTo(event.pos())

            self.viewport().update()

    def mouseReleaseEvent(self, event):
        if self.tool == "Brush" and self.sub_path is not None:
            self.model().setData(self.s_idx, self.sub_path, Qt.UserRole)
            self.sub_path = None
            self.viewport().update()

    def paintEvent(self, event):
        qp = QPainter(self.viewport())
        qp.setPen(self.pen)
        qp.drawPixmap(QPointF(0, 0), self.px_img)
        qp.setOpacity(0.4)
        qp.drawPixmap(QPointF(0, 0), self.px_stack)
        if self.sub_path is not None:
            qp.drawPath(self.sub_path)

    def selectionChanged(self, selected, deselected):
        if selected.indexes() != []:
            self.s_idx = selected.indexes()[0]
            self.pen.setColor(self.model().data(self.s_idx, Qt.DecorationRole))

    def dataChanged(self, top_left, bottom_right, role):
        self.pen.setColor(self.model().data(top_left, Qt.DecorationRole))
        visible = self.model().data(top_left, Qt.CheckStateRole)
        paths = self.model().data(top_left, Qt.UserRole)

        qp = QPainter(self.px_stack)
        qp.setPen(self.pen)
        if not visible:
            qp.setCompositionMode(QPainter.CompositionMode_Clear)

        for path in paths:
            qp.drawPath(path)
        self.viewport().update()
        
    def change_tool(self, action):
        self.tool = action.text()
