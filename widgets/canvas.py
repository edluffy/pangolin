from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter, QPixmap, QPolygonF, QPainterPath, QPen
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QGraphicsScene,
                             QGraphicsView, QLabel, QStackedLayout, QStyle,
                             QTabWidget, QGraphicsPolygonItem)

from widgets.utils import PangoToolBarWidget

class PangoCanvasWidget(QTabWidget):
    def __init__(self, file_s_model, label_s_model, parent=None):
        super().__init__(parent)

        # Models and Views
        self.file_s_model = file_s_model
        self.label_s_model = label_s_model

        self.file_model = file_s_model.model()
        self.label_model = label_s_model.model()

        # Toolbars and menus
        self.tool_bar = PangoToolBarWidget()
        self.parentWidget().addToolBar(Qt.LeftToolBarArea, self.tool_bar)

        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)

        # Widgets

        # Layouts
        
    def new_tab(self, idx):
        title = self.file_model.data(idx, Qt.DisplayRole)
        path = self.file_model.data(idx, Qt.ToolTipRole)
        opened = self.file_model.data(idx, Qt.UserRole+1)

        if opened:
            for i in range(0, self.count()):
                view = self.widget(i)
                if view.path == path:
                    self.setCurrentIndex(self.indexOf(view))
                    return


        view = CanvasView(path)
        view.setModel(self.label_model)
        view.setSelectionModel(self.label_s_model)

        self.file_model.setData(idx, True, Qt.UserRole+1)

        self.tool_bar.action_group.triggered.connect(view.change_tool)

        self.addTab(view, QApplication.style().standardIcon(
            QStyle.SP_ComputerIcon), title)
        self.setCurrentIndex(self.indexOf(view))


class CanvasView(QAbstractItemView):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.s_idx = QtCore.QModelIndex()

        self.path = path
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

    def horizontalOffset(self):
        return self.horizontalScrollBar().value()

    def verticalOffset(self):
        return self.verticalScrollBar().value()

    def moveCursor(self, action, modifiers):
        return QtCore.QModelIndex()
    def indexAt(self, point):
        return QtCore.QModelIndex()
    def visualRect(self, idx):
        return QtCore.QRect()
    def scrollTo(self, idx, hint):
        pass
