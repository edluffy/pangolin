import sys
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
    clear_tool = pyqtSignal()
    clear_changes = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stack = QUndoStack()
        self.fpath = None
        self.active_label = PangoGraphic()
        self.active_com = CreateShape(PangoGraphic, QPointF(), PangoGraphic())

        self.tool = None
        self.tool_size = 10

        self.full_clear()

    def full_clear(self):
        self.stack.clear()
        self.clear()
        self.init_reticle()
        self.reset_com()
        self.clear_tool.emit()

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
        if type(self.active_com.gfx) is PangoPolyGraphic:
            if not self.active_com.gfx.poly.isClosed():
                self.unravel_shape(self.active_com.gfx)
        self.active_com = CreateShape(PangoGraphic, QPointF(), PangoGraphic())

    # Undo all commands for shape (including creation)
    def unravel_shape(self, gfx):
        for i in range(self.stack.count()-1, -1, -1):
            com = self.stack.command(i)
            if com.gfx == gfx:
                com.setObsolete(True)
                if type(com) == CreateShape:
                    break # Reached shape creation
        self.stack.setIndex(0)
        self.stack.setIndex(self.stack.count())

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
        if event.type() == QEvent.GraphicsSceneMousePress and event.buttons() & Qt.LeftButton:
            gfx = self.itemAt(event.scenePos(), QTransform())
            if type(gfx) is PangoPolyGraphic:
                min_dx = float("inf")
                for i in range(0, gfx.poly.count()):
                    dx = QLineF(gfx.poly.value(i), event.scenePos()).length()
                    min_dx = min(dx, min_dx)

                if min_dx < 20:
                    idx = gfx.poly.index(min_dx)
                    self.active_com = MoveShape(event.scenePos(), gfx, idx=idx)
                    self.stack.push(self.active_com)        

            elif type(gfx) is PangoBboxGraphic:
                pass

        elif event.type() == QEvent.GraphicsSceneMouseMove and event.buttons() & Qt.LeftButton:
            if type(self.active_com) is MoveShape:
                if type(self.active_com.gfx) is PangoPolyGraphic: 
                    self.active_com.pos = event.scenePos()

                elif type(self.active_com.gfx) is PangoBboxGraphic: 
                    pass
                    # Prevent inside out bbox
                    #if type(gfx) is PangoBboxGraphic:
                    #    tl = gfx.points[(1, 0)[idx]]
                    #    br = event.scenePos()
                    #    if br.x() < tl.x() or br.y() < tl.y():
                    #        return


        elif event.type() == QEvent.GraphicsSceneMouseRelease:
            self.reset_com()

    def path_handler(self, event):
        if event.type() == QEvent.GraphicsSceneMousePress:
            if type(self.active_com.gfx) is not PangoPathGraphic:
                self.active_com = CreateShape(PangoPathGraphic, event.scenePos(), self.active_label)
                self.stack.push(self.active_com)

            self.stack.beginMacro("Extended "+self.active_com.gfx.name)
            self.active_com = ExtendShape(event.scenePos(), self.active_com.gfx, "moveTo")
            self.stack.push(self.active_com)

        elif event.type() == QEvent.GraphicsSceneMouseMove:
            self.reticle.setPos(event.scenePos())
            if event.buttons() & Qt.LeftButton:
                if type(self.active_com.gfx) is PangoPathGraphic:
                    self.active_com = ExtendShape(event.scenePos(), self.active_com.gfx, "lineTo")
                    self.stack.push(self.active_com)

        elif event.type() == QEvent.GraphicsSceneMouseRelease:
            self.stack.endMacro()

    def poly_handler(self, event):
        if event.type() == QEvent.GraphicsSceneMousePress:
            if type(self.active_com.gfx) is not PangoPolyGraphic:
                self.active_com = CreateShape(PangoPolyGraphic, event.scenePos(), self.active_label)
                self.stack.push(self.active_com)

            if self.active_com.gfx.poly.count() <= 1 or not self.active_com.gfx.poly.isClosed():
                if QLineF(event.scenePos(), self.active_com.gfx.poly.first()).length() < 20:
                    pos = QPointF()
                    pos.setX(self.active_com.gfx.poly.first().x())
                    pos.setY(self.active_com.gfx.poly.first().y())
                else:
                    pos = event.scenePos()

                self.active_com = ExtendShape(pos, self.active_com.gfx)
                self.stack.push(self.active_com)

                if self.active_com.gfx.poly.count() > 1 and self.active_com.gfx.poly.isClosed():
                    self.reset_com()

    def bbox_handler(self, event):
        if event.type() == QEvent.GraphicsSceneMousePress:
            if type(self.active_com.gfx) is not PangoBboxGraphic:
                self.active_com = CreateShape(PangoBboxGraphic, event.scenePos(), self.active_label)
                self.stack.push(self.active_com)

                self.active_com = MoveShape(event.scenePos(), self.active_com.gfx, corner="topLeft")
                self.stack.push(self.active_com)        

        elif event.type() == QEvent.GraphicsSceneMouseMove:
            if event.buttons() & Qt.LeftButton:  
                if type(self.active_com.gfx) is PangoBboxGraphic:
                    pass

                    ## Prevent inside out bbox
                    #tl = self.active_com.gfx.points[0]
                    #br = event.scenePos()
                    #if br.x() > tl.x() and br.y() > tl.y():
                    #    self.active_com = MoveShape(event.scenePos(), 1, self.active_com.gfx)
                    #    self.stack.push(self.active_com)        

        elif event.type() == QEvent.GraphicsSceneMouseRelease:
            if type(self.active_com) is MoveShape:
                pass
                #ps = self.active_com.gfx.points
                #if ps[0] == QPointF() or ps[1] == QPointF() or\
                #QLineF(ps[0], ps[1]).length() <= self.active_com.gfx.dynamic_width()*2:
                #    self.unravel_shape(self.active_com.gfx)
                #self.reset_com()

class CreateShape(QUndoCommand):
    def __init__(self, clss, pos, p_gfx):
        super().__init__()
        self.clss = clss
        self.pos = pos
        self.p_gfx = p_gfx

        self.gfx = self.clss()

    def redo(self):
        self.gfx.setParentItem(self.p_gfx)
        self.gfx.name = self.shape_name()+" at "+self.shape_coords()
        self.gfx.visible = True

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
        return "("+str(round(self.pos.x()))\
              +", "+str(round(self.pos.y()))+")"

class ExtendShape(QUndoCommand):
    def __init__(self, pos, gfx, motion=None):
        super().__init__()
        self.gfx = gfx
        self.pos = pos
        self.motion = motion

    def redo(self):
        self.gfx.scene().active_com = self
        self.gfx.prepareGeometryChange()

        if type(self.gfx) is PangoPathGraphic:
           getattr(self.gfx.path, self.motion)(self.pos)

        elif type(self.gfx) is PangoPolyGraphic:
            self.gfx.poly += self.pos

        self.gfx.update()

        self.setText("Extended "+self.gfx.name+" to ("
            +str(round(self.pos.x()))+", "+str(round(self.pos.y()))+")")

    def undo(self):
        self.gfx.scene().active_com = self
        self.gfx.prepareGeometryChange()

        if type(self.gfx) is PangoPathGraphic:
            ele = self.gfx.path.elementAt(self.gfx.path.elementCount())
            del ele

        elif type(self.gfx) is PangoPolyGraphic:
            self.gfx.poly.remove(self.gfx.poly.count()-1)

        self.gfx.update()

class MoveShape(QUndoCommand):
    def __init__(self, pos, gfx, idx=None, corner=None):
        super().__init__()
        self.gfx = gfx
        self.pos = pos
        self.idx = idx
        self.corner = corner

    def redo(self):
        self.gfx.scene().active_com = self
        self.gfx.prepareGeometryChange()

        if type(self.gfx) is PangoPolyGraphic:
            self.old_pos = self.gfx.poly.value(self.idx)
            self.gfx.poly.replace(self.idx, self.pos)

        elif type(self.gfx) is PangoBboxGraphic:
            self.oldpos = getattr(self.gfx.rect, "corner")
            getattr(self.gfx.rect, "move"+"corner")(self.pos)

        self.gfx.update()

        self.setText("Moved point in "+self.gfx.name+" to ("
            +str(round(self.pos.x()))+", "+str(round(self.pos.y()))+")")

    def undo(self):
        self.gfx.scene().active_com = self
        self.gfx.prepareGeometryChange()

        if type(self.gfx) is PangoPolyGraphic:
            self.gfx.poly.replace(self.idx, self.old_pos)

        elif type(self.gfx) is PangoBboxGraphic:
            getattr(self.gfx.rect, "move"+"corner")(self.old_pos)

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
        self.scene().clear_changes.emit()
        if self.scene().stack.count() == 0:
            for gfx in self.scene().selectedItems():
                self.scene().removeItem(gfx)
                self.scene().gfx_removed.emit(gfx)
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
