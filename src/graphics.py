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
        self.undo_stack = QUndoStack()
        self.last_com = None
        self.fpath = None
        self.label = PangoGraphic()

        self.tool = None
        self.tool_size = 10

        self.full_clear()

    def full_clear(self):
        self.undo_stack.clear()
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
        #TODO: Create general way to stop command halfway
        #if type(self.last_com) is ExtendPoly:
        #    if not self.last_com.gfx.closed:
        #        while type(self.undo_stack.command(self.undo_stack.index()-1)) \
        #               in (ExtendPoly, CreatePoly):
        #            self.undo_stack.undo()
        #            self.undo_stack.command(self.undo_stack.index()).setObsolete(True)

                # Refresh changes made to stack
        #        self.undo_stack.push(QUndoCommand())
        #        self.undo_stack.undo()
        self.last_com = None

    def mousePressEvent(self, event):
        pos = event.scenePos()

        if self.tool in ("Pan", "Lasso"):
            super().mousePressEvent(event)

        elif self.tool == "Path":
            if type(self.last_com) is not ExtendShape:
                self.last_com = CreateShape(self.label, PangoPathGraphic,
                        {'pos': pos, 'width': self.tool_size})
                self.undo_stack.push(self.last_com)

            ## START PATH EXTENSION MACRO
            self.undo_stack.beginMacro("Extended "+self.last_com.gfx.name) 
            self.last_com = ExtendShape(self.last_com.gfx, 
                    {'pos': pos, 'motion': "move"})
            self.undo_stack.push(self.last_com)

        elif self.tool == "Poly":
            if type(self.last_com) is not ExtendShape:
                self.last_com = CreateShape(self.label, PangoPolyGraphic,
                        {'pos': pos})
                self.undo_stack.push(self.last_com)

            self.last_com = ExtendShape(self.last_com.gfx, {'pos': pos})
            self.undo_stack.push(self.last_com)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        pos = event.scenePos()

        if self.tool in ("Pan", "Lasso"):
            pass

        elif self.tool == "Path":
            self.reticle.setPos(pos)
            if event.buttons() & Qt.LeftButton:
                if type(self.last_com) is ExtendShape:
                    self.last_com = ExtendShape(self.last_com.gfx,
                            {'pos': pos, 'motion': "line"})
                    self.undo_stack.push(self.last_com)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.tool in ("Pan", "Lasso"):
            pass

        ## END PATH EXTENSION MACRO
        if self.tool == "Path":
            self.undo_stack.endMacro()

        #if self.tool in ("Pan", "Lasso"):
        #    super().mousePressEvent(event)
        #    gfx = self.itemAt(pos, QTransform())
        #    if type(gfx) is PangoPolyGraphic:
        #        distances = []
        #        for point in gfx.points:
        #            distances.append(QLineF(point, pos).length())

        #        if min(distances) < 20:
        #            p_idx = distances.index(min(distances))

        #            self.undo_stack.endMacro()
        #            self.undo_stack.beginMacro(
        #                    "Moving Point at "+str(pos.x())+", "+str(pos.y())+")")
        #            self.last_com = MovePointPoly(gfx, p_idx, pos)
        #            self.undo_stack.push(self.last_com)

        #elif self.tool == "Path":
        #    if type(self.last_com) is not ExtendPath:
        #        self.last_com = CreatePath(self.label, self.tool_size, pos)
        #        self.undo_stack.push(self.last_com)

        #    self.undo_stack.endMacro()
        #    self.undo_stack.beginMacro("Extended Path to ("+str(pos.x())+", "+str(pos.y())+")")
        #    self.last_com = ExtendPath(self.last_com.gfx, pos, "move")
        #    self.undo_stack.push(self.last_com)

        #elif self.tool == "Poly":
        #    if type(self.last_com) is not ExtendPoly:
        #        self.last_com = CreatePoly(self.label, pos)
        #        self.undo_stack.push(self.last_com)

        #    self.last_com = ExtendPoly(self.last_com.gfx, [pos])
        #    self.undo_stack.push(self.last_com)

        #    if self.last_com.gfx.closed:
        #        points = self.last_com.gfx.points.copy()
        #        points.append(pos)

        #        while type(self.undo_stack.command(self.undo_stack.index()-1)) is ExtendPoly:
        #            self.undo_stack.undo()
        #        self.undo_stack.push(ExtendPoly(self.last_com.gfx, points))
        #        self.tool_reset.emit()
        #        self.reset_com()

    #def mouseMoveEvent(self, event):
    #    super().mouseMoveEvent(event)
    #    pos = event.scenePos()

    #    if self.tool in ("Pan", "Lasso"):
    #        if event.buttons() & Qt.LeftButton and type(self.last_com) is MovePointPoly:
    #            gfx = self.last_com.gfx
    #            p_idx = self.last_com.p_idx
    #            self.last_com = MovePointPoly(gfx, p_idx, pos)
    #            self.undo_stack.push(self.last_com)

    #    elif self.tool == "Path":
    #        self.reticle.setPos(pos)
    #        if event.buttons() & Qt.LeftButton:
    #            if type(self.last_com) is ExtendPath:
    #                self.last_com = ExtendPath(self.last_com.gfx, pos, "line")
    #                self.undo_stack.push(self.last_com)

    #def mouseReleaseEvent(self, event):
    #    super().mouseReleaseEvent(event)
    #    if self.tool in ("Pan", "Lasso"):
    #        if self.last_com is MovePointPoly:
    #            self.undo_stack.endMacro()

    #    if self.tool == "Path":
    #        self.undo_stack.endMacro()

class CreateShape(QUndoCommand):
    def __init__(self, p_gfx, clss, data):
        super().__init__()
        self.p_gfx = p_gfx
        self.clss = clss
        self.data = data
        # Expected data:
        # PangoPathGraphic - 'pos', 'width'
        # PangoPolyGraphic - 'pos' 

    def redo(self):
        self.gfx = self.clss()
        self.gfx.setParentItem(self.p_gfx)
        self.gfx.decorate()

        for attr, val in self.data.items():
            setattr(self.gfx, attr, val)

        p = self.data["pos"]
        n = self.clss.__name__.replace("Pango", "").replace("Graphic", "")
        self.gfx.name = n+" at ("+str(round(p.x()))+", "+str(round(p.y()))+")"
        self.gfx.fpath = self.gfx.scene().fpath

        self.setText("Created "+self.gfx.name)

    def undo(self):
        self.gfx.scene().gfx_removed.emit(self.gfx)
        del self.gfx

class MoveShape(QUndoCommand):
    def __init__(self, gfx, pos):
        super().__init__()
        self.gfx = gfx
        self.pos = pos

    def redo(self):
        pass

    def undo(self):
        pass

class ExtendShape(QUndoCommand):
    def __init__(self, gfx, data):
        super().__init__()
        self.gfx = gfx
        self.data = data
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
            self.gfx.points.append(self.data["pos"])

        self.gfx.update()

    def undo(self):
        self.gfx.prepareGeometryChange()

        if type(self.gfx) is PangoPathGraphic:
            if len(self.gfx.strokes) > 0:
                _, _ = self.gfx.strokes.pop()
        elif type(self.gfx) is PangoPolyGraphic:
            for _ in self.gfx.points:
                if len(self.gfx.points) > 1:
                    self.gfx.points.pop()
            self.gfx.closed = False

        self.gfx.update()


#class CreatePath(QUndoCommand):
#    def __init__(self, p_gfx, tool_size, pos):
#        super().__init__()
#        self.p_gfx = p_gfx
#        self.tool_size = tool_size
#        self.pos = pos
#
#    def redo(self):
#        name = "Path at ("+str(round(self.pos.x()))+", "+str(round(self.pos.y()))+")"
#
#        self.gfx = PangoPathGraphic()
#        self.gfx.setParentItem(self.p_gfx)
#        self.gfx.decorate()
#        self.gfx.setattrs(
#                width=self.tool_size,
#                name=name,
#                fpath=self.gfx.scene().fpath)
#
#        self.setText("+ Created "+name)
#
#    def undo(self):
#        self.gfx.scene().gfx_removed.emit(self.gfx)
#        del self.gfx

#class ExtendPath(QUndoCommand):
#    def __init__(self, gfx, pos, motion):
#        super().__init__()
#        self.gfx = gfx
#        self.pos = pos
#        self.motion = motion
#        
#    def redo(self):
#        self.gfx.prepareGeometryChange()
#        self.gfx.strokes.append((self.pos, self.motion))
#        self.gfx.update()
#
#    def undo(self):
#        self.gfx.prepareGeometryChange()
#        if len(self.gfx.strokes) > 0:
#            _, _ = self.gfx.strokes.pop()
#        self.gfx.update()


#class CreatePoly(QUndoCommand):
#    def __init__(self, p_gfx, pos):
#        super().__init__()
#        self.p_gfx = p_gfx
#        self.pos = pos
#    
#    def redo(self):
#        name = "Poly at ("+str(round(self.pos.x()))+", "+str(round(self.pos.y()))+")"
#
#        self.gfx = PangoPolyGraphic()
#        self.gfx.setParentItem(self.p_gfx)
#        self.gfx.setattrs(
#                color=self.p_gfx.color,
#                name=name,
#                fpath=self.gfx.scene().fpath)
#
#        self.setText("+ Created "+name)
#
#    def undo(self):
#        self.gfx.scene().gfx_removed.emit(self.gfx)
#        del self.gfx

#class ExtendPoly(QUndoCommand):
#    def __init__(self, gfx, points):
#        super().__init__()
#        self.gfx = gfx
#        self.points = points
#
#    def redo(self):
#        self.gfx.prepareGeometryChange()
#        # Check for closure
#        if len(self.gfx.points) > 1:
#            for point in self.points:
#                if QLineF(self.gfx.points[0], point).length() <= self.gfx.w:
#                        self.gfx.closed = True
#
#        if self.gfx.closed:
#            self.setText("Finished "+self.gfx.name)
#        else:
#            self.gfx.points.extend(self.points)
#            coords = "("+str(round(self.points[-1].x())) + \
#                ", "+str(round(self.points[-1].y()))+")"
#            self.setText("Extended Poly to "+coords)
#        self.gfx.update()
#
#    def undo(self):
#        self.gfx.prepareGeometryChange()
#        for _ in self.points:
#            if len(self.gfx.points) > 1:
#                self.gfx.points.pop()
#        self.gfx.closed = False
#        self.gfx.update()

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
