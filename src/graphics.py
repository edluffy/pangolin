from PyQt5.QtCore import QEvent, QLineF, QPoint, QPointF, QRect, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QTransform
from PyQt5.QtWidgets import (QAction, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPixmapItem,
                             QGraphicsScene, QGraphicsView, QMenu, QUndoCommand, QUndoStack)

from item import PangoGraphic, PangoPathGraphic, PangoPolyGraphic, PangoRectGraphic
from utils import pango_get_icon, pango_gfx_change_debug, pango_item_role_debug

from random import randint

class PangoGraphicsScene(QGraphicsScene):
    gfx_changed = pyqtSignal(PangoGraphic, QGraphicsItem.GraphicsItemChange)
    gfx_removed = pyqtSignal(PangoGraphic)
    tool_reset = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.c_stack = QUndoStack()
        self.fpath = None
        self.label = PangoGraphic()

        self.tool = None
        self.tool_size = 10

        self.full_clear()

    def full_clear(self):
        self.c_stack.clear()
        self.clear()
        self.init_reticle()
        self.reset_com()
        self.tool_reset.emit()

    def init_reticle(self):
        self.reticle = QGraphicsEllipseItem(-5, -5, 10, 10)
        self.reticle.setVisible(False)
        self.reticle.setPen(QPen(Qt.NoPen))
        self.addItem(self.reticle)

    def update_reticle(self):
        self.reticle.setBrush(self.label.color)

    def drawBackground(self, painter, rect):
        px = QPixmap(self.fpath)
        painter.drawPixmap(0, 0, px)

    def reset_com(self):
        if type(self.focus_shape()) is PangoPolyGraphic:
            if not self.focus_shape().closed:
                self.unravel_shape()

        while self.focus_shape() is not None:
            self.focus_shape().setSelected(False)

    # Undo all commands for last shape (including creation)
    def unravel_shape(self):
        while type(self.c_stack.command(self.c_stack.index()-1))\
                is not CreateShape:
            self.c_stack.undo()
            self.c_stack.command(self.c_stack.index()).setObsolete(True)

        self.c_stack.undo() # Remove CreateShape
        self.c_stack.command(self.c_stack.index()).setObsolete(True)
        self.c_stack.push(QUndoCommand()) # Refresh changes made to stack
        self.c_stack.undo()

    def focus_shape(self):
        if len(self.selectedItems()) > 0:
            return self.selectedItems()[0]
        else:
            return None

    def c_stack_top(self):
        if len(self.c_stack) > 0:
            return self.c_stack.command(self.c_stack.index()-1)
        else:
            return CreateShape()
    
    def e_stack_top(self):
        return self.c_stack_top().e_stack.command(self.c_stack.index()-1)

    def mousePressEvent(self, event):
        pos = event.scenePos()

        if self.tool in ("Pan", "Lasso"):
            super().mousePressEvent(event)

        elif self.tool == "Path":
            if self.c_stack_top().clss is not PangoPathGraphic:
                self.c_stack.push(CreateShape(PangoPathGraphic, 
                    {'pos': pos, 'width': self.tool_size}, self))

            self.c_stack_top().e_stack.push(
                    ExtendShape({'pos': pos, 'motion': "move"}, self.c_stack_top().gfx))

        elif self.tool == "Poly":
            if self.c_stack_top().clss is not PangoPolyGraphic:
                self.c_stack.push(
                        CreateShape(PangoPolyGraphic, {'pos': pos}, self))

            self.c_stack_top().e_stack.push(
                    ExtendShape({'pos': pos}, self.c_stack_top().gfx))

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        pos = event.scenePos()

        if self.tool in ("Pan", "Lasso"):
            gfx = self.itemAt(pos, QTransform())
            #if hasattr(gfx, "points"):
            #    distances = []
            #    for point in gfx.points:
            #        distances.append(QLineF(point, pos).length())

            #    if min(distances) < 20:
            #        idx = distances.index(min(distances))

            #        ## START MOVE POINT MACRO
            #        self.c_stack.beginMacro(
            #                "Moved point "+str(idx)+" in "+self.gfx.name)
            #        self.last_com = MovePointShape(gfx, idx, pos)
            #        self.c_stack.push(self.last_com)        

        elif self.tool == "Path":
            self.reticle.setPos(pos)
            if event.buttons() & Qt.LeftButton and self.c_stack_top().clss is PangoPathGraphic:
                self.c_stack_top().e_stack.push(
                        ExtendShape({'pos': pos, 'motion': "line"}, self.c_stack_top().gfx))

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.tool in ("Pan", "Lasso"):
            pass

class CreateShape(QUndoCommand):
    def __init__(self, clss=None, data=None, scene=None):
        super().__init__()
        self.scene = scene
        self.clss = clss
        self.data = data
        # Expected data:
        # PangoPathGraphic - 'pos', 'width'
        # PangoPolyGraphic - 'pos' 

        if (self.clss and self.data) is not None:
            self.gfx = self.clss()
            self.gfx.setParentItem(self.scene.label)
            self.gfx.decorate()
            for attr, val in self.data.items():
                setattr(self.gfx, attr, val)

            self.set_text()

        self.e_stack = QUndoStack()

    def redo(self):
        self.gfx.setSelected(True)
        self.scene.addItem(self.gfx)

        self.e_stack.setIndex(self.e_stack.count()-1)

    def undo(self):
        self.gfx.setSelected(False)
        self.scene.removeItem(self.gfx)
        self.scene.gfx_removed.emit(self.gfx)
        #del self.gfx

        self.e_stack.setIndex(0)
        print(self.e_stack.count())

    def set_text(self):
        p = self.data["pos"]
        n = self.clss.__name__.replace("Pango", "").replace("Graphic", "")
        self.gfx.name = n+" at ("+str(round(p.x()))+", "+str(round(p.y()))+")"
        self.gfx.fpath = self.gfx.scene().fpath
        self.setText("Created "+self.gfx.name)


class ExtendShape(QUndoCommand):
    def __init__(self, data=None, gfx=None):
        super().__init__()
        self.data = data
        self.gfx = gfx
        # Expected data:
        # PangoPathGraphic - 'pos', 'motion'
        # PangoPolyGraphic - 'pos'

    def redo(self):
        self.gfx.prepareGeometryChange()

        if type(self.gfx) is PangoPathGraphic:
            self.gfx.strokes.append((self.data["pos"], self.data["motion"]))

        elif type(self.gfx) is PangoPolyGraphic:
            if len(self.gfx.points) > 1: # Check for closure
                if QLineF(self.gfx.points[0], self.data["pos"]).length() <= self.gfx.w:
                    self.gfx.closed = True

            if self.gfx.closed:
                self.setText("Finished "+self.gfx.name)
            else:
                p = self.data["pos"]
                self.gfx.points.append(p)
                self.setText("Extended "+self.gfx.name+" to ("
                        +str(round(p.x()))+", "+str(round(p.y()))+")")

        self.gfx.update()

    def undo(self):
        self.gfx.prepareGeometryChange()

        if type(self.gfx) is PangoPathGraphic:
            _, _ = self.gfx.strokes.pop()

        elif type(self.gfx) is PangoPolyGraphic:
            if self.gfx.closed:
                self.gfx.closed = False
            else:
                _ = self.gfx.points.pop()

        self.gfx.update()

class MovePointShape(QUndoCommand):
    def __init__(self, data=None, scene=None):
        super().__init__()
        self.scene = scene
        self.data = data
        # Expected data:
        # PangoPolyGraphic - 'pos', 'idx'
        # PangoRectGraphic - 'pos', 'idx'

    def redo(self):
        gfx = self.scene.focus_shape()
        gfx.prepareGeometryChange()

        self.data["old_pos"] = self.gfx.points[self.data["idx"]]
        gfx.points[self.data["idx"]] = self.data["pos"]

        gfx.update()

    def undo(self):
        gfx = self.scene.focus_shape()
        gfx.prepareGeometryChange()

        gfx.points[self.data["idx"]] = self.data["old_pos"]

        gfx.update()


class MovePointPoly(QUndoCommand):
    def __init__(self, gfx, p_idx, pos):
        super().__init__()
        self.gfx = gfx
        self.pos = pos
        self.p_idx = p_idx

    def redo(self):
        self.old_pos = self.gfx.points[self.p_idx]
        self.gfx.prepareGeometryChange()
        self.gfx.points[self.p_idx] = self.pos
        self.gfx.update()

    def undo(self):
        self.gfx.prepareGeometryChange()
        self.gfx.points[self.p_idx] = self.old_pos
        self.gfx.update()

class PangoGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setInteractive(True)
        self.setMouseTracking(True)
        self.setCacheMode(QGraphicsView.CacheBackground)
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
            self.coords+=item.name

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
            names = ', '.join([gfx.name for gfx in self.scene().selectedItems()])

            self.del_action = QAction("Delete "+names+"?")
            self.del_action.setIcon(pango_get_icon("trash"))
            self.del_action.triggered.connect(self.delete_selected)

            menu.addAction(self.del_action)
            menu.exec(event.globalPos())
