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
        self.stack = QUndoStack()
        self.fpath = None
        self.label = PangoGraphic()
        self.shape = PangoGraphic()

        self.tool = None
        self.tool_size = 10

        self.full_clear()

    def full_clear(self):
        self.stack.clear()
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
        while type(self.stack.command(self.stack.index()-1))\
                is not CreateShape:
            self.stack.undo()
            self.stack.command(self.stack.index()).setObsolete(True)

        self.stack.undo() # Remove CreateShape
        self.stack.command(self.stack.index()).setObsolete(True)
        self.stack.push(QUndoCommand()) # Refresh changes made to stack

        print(self.stack.command(self.stack.index()))

    def focus_shape(self):
        if len(self.selectedItems()) > 0:
            return self.selectedItems()[0]
        else:
            return None

    def event(self, event):
        if self.tool == "Path":
            self.path_handler(event)
        if self.tool == "Poly":
            self.poly_handler(event)
        return False
    
    def path_handler(self, event):
        if event.type() == QEvent.GraphicsSceneMousePress:
            if type(self.shape) is not PangoPathGraphic:
                self.stack.push(CreateShape(PangoPathGraphic, 
                    {'pos': event.scenePos(), 'width': self.tool_size}, self))

            self.stack.push(ExtendPath(event.scenePos(), "move", self.shape))

        elif event.type() == QEvent.GraphicsSceneMouseMove:
            self.reticle.setPos(event.scenePos())
            if event.buttons() & Qt.LeftButton and type(self.shape) is PangoPathGraphic:
                self.stack.push(ExtendPath(event.scenePos(), "line", self.shape))

        elif event.type() == QEvent.GraphicsSceneMouseRelease:
            pass

    def poly_handler(self, event):
        if event.type() == QEvent.GraphicsSceneMousePress:
            if type(self.shape) is not PangoPolyGraphic:
                self.stack.push(
                        CreateShape(PangoPolyGraphic, {'pos': event.scenePos()}, self))

            self.stack.push(ExtendPoly(event.scenePos(), self.shape))

        elif event.type() == QEvent.GraphicsSceneMouseMove:
            pass

        elif event.type() == QEvent.GraphicsSceneMouseRelease:
            pass

            #gfx = self.itemAt(pos, QTransform())
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


class CreateShape(QUndoCommand):
    def __init__(self, clss, data, scene=None):
        super().__init__()
        self.scene = scene
        self.clss = clss
        self.data = data
        # Expected data:
        # PangoPathGraphic - 'pos', 'width'
        # PangoPolyGraphic - 'pos' 

    def redo(self):
        self.gfx = self.clss()
        self.copy_data()
        self.gfx.setSelected(True)

        self.scene.shape = self.gfx
        self.setText("Created "+self.shape_name()+" at "+self.shape_coords())

    def undo(self):
        self.gfx.setSelected(False)
        self.scene.removeItem(self.gfx)
        self.scene.gfx_removed.emit(self.gfx)
        del self.gfx

    def copy_data(self):
        self.gfx.setParentItem(self.scene.label)
        self.gfx.name = self.shape_name()+" at "+self.shape_coords()
        self.gfx.fpath = self.gfx.scene().fpath
        self.gfx.decorate()
        for attr, val in self.data.items():
            setattr(self.gfx, attr, val)

    def shape_name(self):
        if self.clss is not None:
            return self.clss.__name__.replace("Pango", "").replace("Graphic", "")
        else:
            return "Undefined"

    def shape_coords(self):
        if self.data["pos"] is not None:
            return " at ("+str(round(self.data["pos"].x()))\
                  +", "+str(round(self.data["pos"].y()))+")"
        else:
            return "(~, ~)"

class ExtendPath(QUndoCommand):
    def __init__(self, pos, motion, gfx):
        super().__init__()
        self.gfx = gfx
        self.pos = pos
        self.motion = motion

    def redo(self):
        self.gfx.prepareGeometryChange()
        self.gfx.strokes.append((self.pos, self.motion))
        self.gfx.update()

    def undo(self):
        self.gfx.prepareGeometryChange()
        _, _ = self.gfx.strokes.pop()
        self.gfx.update()

class ExtendPoly(QUndoCommand):
    def __init__(self, pos, gfx):
        super().__init__()
        self.gfx = gfx
        self.pos = pos

    def redo(self):
        self.gfx.prepareGeometryChange()
        if len(self.gfx.points) > 1: # Check for closure
            if QLineF(self.gfx.points[0], self.pos).length() <= self.gfx.w:
                self.gfx.closed = True

        if self.gfx.closed:
            self.setText("Finished "+self.gfx.name)
        else:
            p = self.pos
            self.gfx.points.append(p)
            self.setText("Extended "+self.gfx.name+" to ("
                    +str(round(p.x()))+", "+str(round(p.y()))+")")
        self.gfx.update()

    def undo(self):
        self.gfx.prepareGeometryChange()
        if self.gfx.closed:
            self.gfx.closed = False
        else:
            _ = self.gfx.points.pop()
        self.gfx.update()

class MovePointShape(QUndoCommand):
    def __init__(self, pos, idx, gfx):
        super().__init__()
        self.gfx = gfx
        self.pos = pos
        self.idx = idx

    def redo(self):
        self.gfx.prepareGeometryChange()
        self.old_pos = self.gfx.points[self.idx]
        self.gfx.points[self.idx] = self.pos
        self.gfx.update()

    def undo(self):
        self.gfx.prepareGeometryChange()
        self.gfx.points[self.idx] = self.old_pos
        self.gfx.update()


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
