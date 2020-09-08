from PyQt5.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PyQt5.QtWidgets import (QAction, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPixmapItem,
                             QGraphicsScene, QGraphicsView, QMenu, QUndoCommand, QUndoStack)

from item import (PangoPointGraphic, PangoGraphic, PangoPathGraphic,
                  PangoPolyGraphic, PangoRectGraphic)
from utils import PangoShapeType, pango_get_icon, pango_gfx_change_debug, pango_item_role_debug

import copy


class PangoGraphicsScene(QGraphicsScene):
    gfx_changed = pyqtSignal(PangoGraphic, QGraphicsItem.GraphicsItemChange)
    gfx_removed = pyqtSignal(PangoGraphic)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 100, 100)
        self.undo_stack = QUndoStack()
        self.last_com = None

        self.label = PangoGraphic()
        self.tool = None
        self.tool_size = 10

        self.reticle = QGraphicsEllipseItem(-5, -5, 10, 10)
        self.reticle.setVisible(False)
        self.reticle.setPen(QPen(Qt.NoPen))
        self.addItem(self.reticle)

    def change_image(self, idx):
        path = idx.model().filePath(idx)

        for item in self.items():
            if item.type == QGraphicsPixmapItem():
                self.removeItem(item)
        new_item = self.addPixmap(QPixmap(path))
        new_item.setZValue(-1)

    def set_label(self, label):
        self.label = label
        self.reset_com()

        self.reticle.setBrush(self.label.decoration()[1])

    def set_tool(self, action):
        self.tool = action.text()
        self.reset_com()

        self.reticle.setVisible(self.tool == "Path")
        self.views()[0].set_cursor(self.tool)

    def set_tool_size(self, size_select):
        size = size_select.value()
        self.tool_size = size
        self.reset_com()

        view = self.views()[0]
        x = size_select.geometry().center().x()
        y = view.rect().top() + size/2
        self.reticle.setRect(-size/2, -size/2, size, size)
        self.reticle.setPos(view.mapToScene(QPoint(x, y)))

    def reset_tool(self):
        self.set_tool(QAction("Lasso"))
        self.reset_com()

    def reset_com(self):
        if type(self.last_com) is ExtendPoly:
            if not self.last_com.gfx.closed():
                while type(self.undo_stack.command(self.undo_stack.index()-1)) is ExtendPoly:
                    self.undo_stack.command(self.undo_stack.index()-1).setObsolete(True)
                    self.undo_stack.undo()

                self.undo_stack.command(self.undo_stack.index()-1).setObsolete(True)
                self.undo_stack.undo()
                self.removeItem(self.last_com.gfx)
        self.last_com = None

    def mousePressEvent(self, event):
        pos = event.scenePos()

        if self.tool == "Pan" or self.tool == "Lasso":
            super().mousePressEvent(event)

        elif self.tool == "Path":
            if type(self.last_com) is not ExtendPath:
                self.last_com = CreatePath(self.label, self.tool_size, pos)
                self.undo_stack.push(self.last_com)

            self.undo_stack.beginMacro("Path extension at ("+str(pos.x())+", "+str(pos.y())+")")
            self.last_com = ExtendPath(self.last_com.gfx, pos, 1)
            self.undo_stack.push(self.last_com)

        elif self.tool == "Poly":
            if type(self.last_com) is not ExtendPoly:
                self.last_com = CreatePoly(self.label, pos)
                self.undo_stack.push(self.last_com)

            self.last_com = ExtendPoly(self.last_com.gfx, [pos])
            self.undo_stack.push(self.last_com)

            if self.last_com.gfx.closed():
                points = self.last_com.gfx.points()
                points.append(pos)

                while type(self.undo_stack.command(self.undo_stack.index()-1)) is ExtendPoly:
                    self.undo_stack.undo()
                self.undo_stack.push(ExtendPoly(self.last_com.gfx, points))
                self.reset_tool()


    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        pos = event.scenePos()

        if self.tool == "Path":
            self.reticle.setPos(pos)
            if event.buttons() & Qt.LeftButton:
                if type(self.last_com) is ExtendPath:
                    self.last_com = ExtendPath(self.last_com.gfx, pos, 0)
                    self.undo_stack.push(self.last_com)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.tool == "Path":
            self.undo_stack.endMacro()


class CreatePath(QUndoCommand):
    def __init__(self, p_gfx, tool_size, pos):
        super().__init__()
        self.p_gfx = p_gfx
        self.tool_size = tool_size
        self.pos = pos

    def redo(self):
        name = "Path at ("+str(round(self.pos.x()))+", "+str(round(self.pos.y()))+")"

        self.gfx = PangoPathGraphic()
        self.gfx.setParentItem(self.p_gfx)
        self.gfx.set_decoration()
        self.gfx.set_width(self.tool_size)
        self.gfx.set_name(name)
        self.setText("Created "+name)

    def undo(self):
        self.gfx.scene().gfx_removed.emit(self.gfx)
        del self.gfx

class ExtendPath(QUndoCommand):
    def __init__(self, gfx, pos, action):
        super().__init__()
        self.gfx = gfx
        self.pos = pos
        self.action = action
        
    def redo(self):
        self.gfx.add_point(self.pos, self.action)
        self.gfx.update()

    def undo(self):
        _, _ = self.gfx.pop_point()
        self.gfx.update()


class CreatePoly(QUndoCommand):
    def __init__(self, p_gfx, pos):
        super().__init__()
        self.p_gfx = p_gfx
        self.pos = pos
    
    def redo(self):
        name = "Poly at ("+str(round(self.pos.x()))+", "+str(round(self.pos.y()))+")"

        self.gfx = PangoPolyGraphic()
        self.gfx.setParentItem(self.p_gfx)
        self.gfx.set_decoration()
        self.gfx.set_name(name)
        self.setText("Created "+name)

    def undo(self):
        self.gfx.scene().gfx_removed.emit(self.gfx)
        del self.gfx

class ExtendPoly(QUndoCommand):
    def __init__(self, gfx, points):
        super().__init__()
        self.gfx = gfx
        self.points = points

    def redo(self):
        for point in self.points:
            self.gfx.add_point(point)
        self.gfx.update()

        if self.gfx.closed():
            self.setText("Finished "+self.gfx.name())
        else:
            coords = "("+str(round(self.points[-1].x())) + \
                ", "+str(round(self.points[-1].y()))+")"
            self.setText("Extended Poly to "+coords)

    def undo(self):
        for _ in self.points:
            self.gfx.rem_point()
        self.gfx.update()

class PangoGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setInteractive(True)
        self.setMouseTracking(True)
        self.coords = ""

    def set_cursor(self, tool):
        if tool == "Pan":
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        elif tool == "Lasso":
            self.setCursor(Qt.ArrowCursor)
            self.setDragMode(QGraphicsView.RubberBandDrag)
        elif tool == "Path":
            self.setCursor(Qt.BlankCursor)
            self.setDragMode(QGraphicsView.NoDrag)
        elif tool == "Rect":
            self.setCursor(Qt.CrossCursor)
            self.setDragMode(QGraphicsView.NoDrag)
        elif tool == "Poly":
            self.setCursor(Qt.CrossCursor)
            self.setDragMode(QGraphicsView.NoDrag)

    def delete_selected(self):
        for gfx in self.scene().selectedItems():
            self.scene().removeItem(gfx)

    def paintEvent(self, event):
        super().paintEvent(event)
        qp = QPainter(self.viewport())
        qp.setFont(QFont("Arial", 10))

        vrect = self.viewport().rect()
        text_box = QRectF(QPoint(vrect.right()-100, 0), QPoint(vrect.right(), 50))
        qp.drawText(text_box, Qt.AlignRight, self.coords)

        self.viewport().update()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        pos = self.mapToScene(event.pos())
        self.coords = "x: "+str(round(pos.x()))+"\ny: "+str(round(pos.y()))+"\n"

        item = self.itemAt(event.pos())
        if hasattr(item, "name"):
            self.coords+=item.name()

    def wheelEvent(self, event):
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        zoom = 1.05

        old_pos = self.mapToScene(event.pos())
        if event.angleDelta().y() > 0:
            self.scale(zoom, zoom)
        else:
            self.scale(1/zoom, 1/zoom)
        new_pos = self.mapToScene(event.pos())

        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        gfx = self.itemAt(event.pos())
        if gfx is not None:
            gfx.setSelected(True)
            names = ', '.join([gfx.name() for gfx in self.scene().selectedItems()])

            self.del_action = QAction("Delete "+names+"?")
            self.del_action.setIcon(pango_get_icon("trash"))
            self.del_action.triggered.connect(self.delete_selected)

            menu.addAction(self.del_action)
            menu.exec(event.globalPos())
