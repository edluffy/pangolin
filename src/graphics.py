from PyQt5.QtCore import QEvent, QLineF, QPoint, QPointF, QRect, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QTransform
from PyQt5.QtWidgets import (QAction, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPixmapItem,
                             QGraphicsScene, QGraphicsView, QMenu, QMessageBox, QUndoCommand, QUndoCommand, QUndoStack)

from item import PangoBboxGraphic, PangoGraphic, PangoPathGraphic, PangoPolyGraphic, PangoBboxItem
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
        self.active_label = PangoGraphic()
        self.active_com = QUndoCommand()

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
        self.reticle.setBrush(self.active_label.color)

    def drawBackground(self, painter, rect):
        px = QPixmap(self.fpath)
        painter.drawPixmap(0, 0, px)

    def reset_com(self):
        if hasattr(self.active_com, "gfx"):
            if type(self.active_com.gfx) is PangoPolyGraphic and not self.active_com.gfx.closed:
                self.unravel_active_com()
        self.active_com = None

    # Undo all commands for active shape (including creation)
    def unravel_active_com(self):
        while type(self.stack.command(self.stack.index()-1))\
                is not CreateShape:
            self.stack.undo()
            self.stack.command(self.stack.index()).setObsolete(True)

        self.stack.undo() # Remove CreateShape
        self.stack.command(self.stack.index()).setObsolete(True)

        self.stack.push(QUndoCommand()) # Refresh changes made to stack
        self.stack.undo()

    def event(self, event):
        super().event(event)

        if self.tool == "Lasso":
            self.select_handler(event)
            return False
        elif self.tool == "Path":
            self.path_handler(event)
            return False
        elif self.tool == "Poly":
            self.poly_handler(event)
            return False
        elif self.tool == "Bbox":
            self.bbox_handler(event)
            return False
        else:
            return False

    def select_handler(self, event):
        if event.type() == QEvent.GraphicsSceneMousePress:
            gfx = self.itemAt(event.scenePos(), QTransform())
            if hasattr(gfx, "points") and event.buttons() & Qt.LeftButton:
                distances = []
                for point in gfx.points:
                    distances.append(QLineF(point, event.scenePos()).length())

                if min(distances) < 20:
                    idx = distances.index(min(distances))
                    self.stack.beginMacro("Moved point "+str(idx)+" in "+gfx.name)
                    self.active_com = MovePoint(event.scenePos(), idx, gfx)
                    self.stack.push(self.active_com)        

        elif event.type() == QEvent.GraphicsSceneMouseMove:
            if event.buttons() & Qt.LeftButton and type(self.active_com) is MovePoint:
                idx = self.active_com.idx
                gfx = self.active_com.gfx

                # Prevent inside out bbox
                if type(gfx) is PangoBboxGraphic:
                    tl = gfx.points[(1, 0)[idx]]
                    br = event.scenePos()
                    if br.x() < tl.x() or br.y() < tl.y():
                        return

                self.active_com = MovePoint(event.scenePos(), idx, gfx)
                self.stack.push(self.active_com)        

        elif event.type() == QEvent.GraphicsSceneMouseRelease:
            if type(self.active_com) is MovePoint:
                self.stack.endMacro()
                self.reset_com()

    def path_handler(self, event):
        if event.type() == QEvent.GraphicsSceneMousePress:
            if self.active_com is None or type(self.active_com.gfx) is not PangoPathGraphic:
                self.active_com = CreateShape(
                    PangoPathGraphic, 
                    {'pos': event.scenePos(), 'width': self.tool_size}, self.active_label)
                self.stack.push(self.active_com)

            self.stack.beginMacro("Added stroke to "+self.active_com.gfx.name)
            self.active_com = ExtendPath(event.scenePos(), "move", self.active_com.gfx)
            self.stack.push(self.active_com)

        elif event.type() == QEvent.GraphicsSceneMouseMove:
            self.reticle.setPos(event.scenePos())
            if event.buttons() & Qt.LeftButton and type(self.active_com.gfx) is PangoPathGraphic:
                self.active_com = ExtendPath(event.scenePos(), "line", self.active_com.gfx)
                self.stack.push(self.active_com)

        elif event.type() == QEvent.GraphicsSceneMouseRelease:
            self.stack.endMacro()


    def poly_handler(self, event):
        if event.type() == QEvent.GraphicsSceneMousePress:
            if self.active_com is None or type(self.active_com.gfx) is not PangoPolyGraphic:
                self.active_com = CreateShape(
                        PangoPolyGraphic, {'pos': event.scenePos()}, self.active_label)
                self.stack.push(self.active_com)


            if not self.active_com.gfx.closed:
                self.active_com = ExtendPoly(event.scenePos(), self.active_com.gfx)
                self.stack.push(self.active_com)

    def bbox_handler(self, event):
        if event.type() == QEvent.GraphicsSceneMousePress:
            if self.active_com is None or type(self.active_com.gfx) is not PangoBboxGraphic:
                self.active_com = CreateShape(
                        PangoBboxGraphic, {'pos': event.scenePos()}, self.active_label)
                self.stack.push(self.active_com)

                self.stack.beginMacro("Finished "+self.active_com.gfx.name)
                self.active_com = ExtendBbox(event.scenePos(), 0, self.active_com.gfx)
                self.stack.push(self.active_com)        


        elif event.type() == QEvent.GraphicsSceneMouseMove:
            if event.buttons() & Qt.LeftButton:  
                if hasattr(self.active_com, "gfx") and\
                    type(self.active_com.gfx) is PangoBboxGraphic:

                    # Prevent inside out bbox
                    tl = self.active_com.gfx.points[0]
                    br = event.scenePos()
                    if br.x() > tl.x() and br.y() > tl.y():
                        self.active_com = ExtendBbox(event.scenePos(), 1, self.active_com.gfx)
                        self.stack.push(self.active_com)        

        elif event.type() == QEvent.GraphicsSceneMouseRelease:
            if type(self.active_com) is ExtendBbox:
                self.stack.endMacro()

                ps = self.active_com.gfx.points
                if ps[0] == QPointF() or ps[1] == QPointF() or\
                QLineF(ps[0], ps[1]).length() <= self.active_com.gfx.dynamic_width()*2:
                    self.unravel_active_com()
                self.reset_com()

class CreateShape(QUndoCommand):
    def __init__(self, clss, data, p_gfx):
        super().__init__()
        self.p_gfx = p_gfx
        self.clss = clss
        self.data = data
        # Expected data:
        # PangoPathGraphic - 'pos', 'width'
        # PangoPolyGraphic - 'pos' 
        # PangoBboxGraphic - 'pos' 

        self.gfx = self.clss()

    def redo(self):
        self.gfx.setParentItem(self.p_gfx)
        self.gfx.name = self.shape_name()+" at "+self.shape_coords()
        self.gfx.visible = True
        for attr, val in self.data.items():
            if attr != "pos":
                setattr(self.gfx, attr, val)

        self.gfx.scene().clearSelection()
        self.gfx.setSelected(True)
        self.setText("Created "+self.shape_name()+" at "+self.shape_coords())

    def undo(self):
        scene = self.p_gfx.scene()
        scene.removeItem(self.gfx)
        scene.gfx_removed.emit(self.gfx)

    def shape_name(self):
        return self.clss.__name__.replace("Pango", "").replace("Graphic", "")

    def shape_coords(self):
        return "("+str(round(self.data["pos"].x()))\
              +", "+str(round(self.data["pos"].y()))+")"

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
            if QLineF(self.gfx.points[0], self.pos).length() <= self.gfx.dynamic_width()*2:
                self.gfx.closed = True
                self.gfx.scene().gfx_changed.emit(self.gfx, QGraphicsItem.ItemMatrixChange)

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

class ExtendBbox(QUndoCommand):
    def __init__(self, pos, idx, gfx):
        super().__init__()
        self.gfx = gfx
        self.pos = pos
        self.idx = idx

    def redo(self):
        self.gfx.prepareGeometryChange()
        p = self.pos
        self.gfx.points[self.idx] = p
        self.setText("Extended "+self.gfx.name+" to ("
                +str(round(p.x()))+", "+str(round(p.y()))+")")
        self.gfx.update()

    def undo(self):
        self.gfx.prepareGeometryChange()
        self.gfx.points[self.idx] = QPointF()
        self.gfx.update()

class MovePoint(QUndoCommand):
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
        elif tool == "Bbox":
            self.setCursor(Qt.CrossCursor)
            self.setDragMode(QGraphicsView.NoDrag)
        elif tool == "Poly":
            self.setCursor(Qt.CrossCursor)
            self.setDragMode(QGraphicsView.NoDrag)

    def delete_selected(self):
        res = QMessageBox().question( self, "Unsaved shape commands", 
                "Command history will be cleaned, are you sure you want to continue?")

        if res == QMessageBox.Yes:
            for gfx in self.scene().selectedItems():
                self.scene().removeItem(gfx)
                self.scene().gfx_removed.emit(gfx)
                self.scene().stack.clear()
                self.scene().reset_com()

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
