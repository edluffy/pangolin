from PyQt5.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (QAction, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPixmapItem,
                             QGraphicsScene, QGraphicsView, QMenu)

from item import (PangoDotGraphic, PangoGraphic, PangoPathGraphic,
                  PangoPolyGraphic, PangoRectGraphic)
from utils import PangoShapeType, pango_get_icon, pango_gfx_change_debug, pango_item_role_debug


class PangoGraphicsScene(QGraphicsScene):
    gfx_changed = pyqtSignal(PangoGraphic, QGraphicsItem.GraphicsItemChange)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 100, 100)

        self.label = PangoGraphic()
        self.gfx = None
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
        self.reticle.setBrush(self.label.decoration()[1])

    def set_tool(self, action):
        self.tool = action.text()
        self.reticle.setVisible(self.tool == "Path")
        self.views()[0].set_cursor(self.tool)

    def set_tool_size(self, size_select):
        size = size_select.value()
        self.tool_size = size

        view = self.views()[0]
        x = size_select.geometry().center().x()
        y = view.rect().top() + size/2
        self.reticle.setRect(-size/2, -size/2, size, size)
        self.reticle.setPos(view.mapToScene(QPoint(x, y)))

    def mousePressEvent(self, event):
        if self.tool == "Pan" or self.tool == "Lasso":
            super().mousePressEvent(event)

    def event(self, event):
        super().event(event)
        if self.tool == "Path":
            if event.type() == QEvent.GraphicsSceneMousePress:
                self.gfx = PangoPathGraphic()

                self.gfx.setParentItem(self.label)
                self.gfx.set_width(self.tool_size)
                self.gfx.set_name("Rando Path")
                self.gfx.set_decoration()

                self.gfx.move_to(event.scenePos())
                return True
            if event.type() == QEvent.GraphicsSceneMouseMove:
                if self.gfx is not None:
                    self.gfx.line_to(event.scenePos())
                self.reticle.setPos(event.scenePos())
                return True
            if event.type() == QEvent.GraphicsSceneMouseRelease:
                if self.gfx is not None:
                    for gfx in self.gfx.collidingItems():
                        if gfx.type() == PangoShapeType.Path:
                            self.gfx.merge(gfx)
                    self.gfx = None
                    return True
        return False
 
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
