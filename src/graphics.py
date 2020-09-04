from PyQt5.QtCore import QEvent, QItemSelectionModel, QObject, Qt, pyqtSignal, QRectF, QPoint, QModelIndex, QLineF, QPersistentModelIndex
from PyQt5.QtGui import QColor, QPainterPath, QPixmap, QPolygonF, QPen, QBrush
from PyQt5.QtWidgets import (QAbstractItemView, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem, 
                             QGraphicsPixmapItem, QGraphicsScene, QGraphicsSceneMouseEvent, QGraphicsView)

from bidict import bidict

from item import PangoGraphic, PangoHybridItem, PangoPathGraphic, PangoDotGraphic, PangoPolyGraphic, PangoRectGraphic
from utils import PangoShapeType, pango_gfx_change_debug, pango_item_role_debug

""" PangoModelSceneInterface promotes loose coupling by keeping model/view and 
   scene/view from referring to each other explicitly """
class PangoSceneModelInterface(object):
    tool_reset = pyqtSignal()
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.model.dataChanged.connect(self.item_changed)

        self.map = bidict()

    # Model/View changes (item) ----> Scene/View (gfx)
    def set_view(self, view): # <--- ditch in favour of set_model?
        self.view = view
        self.view.selectionModel().selectionChanged.connect(self.item_selection_changed)

    # Scene/View changes (gfx) ----> Model/View (item)
    def set_scene(self, scene):
        self.scene = scene
        self.scene.gfx_changed.connect(self.gfx_changed)
        self.scene.selectionChanged.connect(self.gfx_selection_changed)

    def item_selection_changed(self):
        new = [self.map[QPersistentModelIndex(idx)] for idx in self.view.selectedIndexes()]
        old = self.scene.selectedItems()

        for gfx in set(new)-set(old):
            gfx.setSelected(True)

        for gfx in set(old)-set(new):
            gfx.setSelected(False)

    def gfx_selection_changed(self):
        new = [QModelIndex(self.map.inverse[gfx]) for gfx in self.scene.selectedItems()]
        old = self.view.selectedIndexes()

        for idx in set(new)-set(old):
            self.view.selectionModel().select(idx, QItemSelectionModel.Select)

        for idx in set(old)-set(new):
            self.view.selectionModel().select(idx, QItemSelectionModel.Deselect)

    def item_changed(self, top_idx, bottom_idx, roles):
        item = self.model.itemFromIndex(top_idx)
        role = roles[0]
        #print("Item change: ", pango_item_role_debug(role))
        try:
            gfx = self.map[item.key()]
        except KeyError:
            gfx = self.create_gfx_from_item(item)

        if role == Qt.DisplayRole:
            gfx.set_name(item.name())
        elif role == Qt.DecorationRole:
            gfx.set_color(item.color())
        elif role == Qt.CheckStateRole:
            gfx.set_visible(item.visible())

    def gfx_changed(self, gfx, change):
        #print("Gfx change: ", pango_gfx_change_debug(change))
        try:
            item = self.model.itemFromIndex(QModelIndex(self.map.inverse[gfx]))
        except KeyError:
            item = self.create_item_from_gfx(gfx)

        if change == QGraphicsItem.ItemToolTipHasChanged:
            item.set_name(gfx.name())
        elif change == QGraphicsItem.ItemTransformHasChanged:
            item.set_color(gfx.color())
        elif change == QGraphicsItem.ItemVisibleHasChanged:
            item.set_visible(gfx.visible())

    def item_removed(self):
        pass

    def gfx_removed(self):
        pass

    def create_item_from_gfx(self, gfx):
        item = PangoHybridItem(gfx.type())

        # Add to model, then map
        if gfx.parentItem() is not None:
            parent_item = self.model.itemFromIndex(QModelIndex(self.map.inverse[gfx.parentItem()]))
            parent_item.appendRow(item)
        else:
            self.model.appendRow(item)
        self.map[item.key()] = gfx
        return item

    def create_gfx_from_item(self, item):
        if item.type() == PangoShapeType.Path:
            gfx = PangoPathGraphic()
        elif item.type() == PangoShapeType.Rect:
            gfx = PangoRectGraphic()
        elif item.type() == PangoShapeType.Poly:
            gfx = PangoPolyGraphic()
        elif item.type() == PangoShapeType.Dot:
            gfx = PangoDotGraphic()
        else:
            gfx = PangoGraphic()

        # Map, then add to scene
        self.map[item.key()] = gfx
        if item.parent() is not None:
            gfx.setParentItem(self.map[item.parent().key()])
        else:
            self.scene.addItem(gfx)
        return gfx

    def set_label(self, row):
        item = self.model.item(row)
        try:
            self.scene.label = self.map[item.key()]
        except KeyError:
            return


class PangoGraphicsScene(QGraphicsScene):
    tool_reset = pyqtSignal()

    gfx_changed = pyqtSignal(PangoGraphic, QGraphicsItem.GraphicsItemChange)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 100, 100)

        self.label = PangoGraphic()
        self.tool_size = 10
        self.tool = None
        self.gfx = None

    def reset_tool(self):
        self.tool_reset.emit()

    def change_image(self, idx):
        path = idx.model().filePath(idx)

        for item in self.items():
            if item.type == QGraphicsPixmapItem():
                self.removeItem(item)
        new_item = self.addPixmap(QPixmap(path))
        new_item.setZValue(-1)

    def change_tool(self, action):
        view = self.views()[0]
        view.setDragMode(QGraphicsView.NoDrag)
        self.tool = action.text()

        if self.tool == "Pan":
            view.setDragMode(QGraphicsView.ScrollHandDrag)
        elif self.tool == "Lasso":
            view.setDragMode(QGraphicsView.RubberBandDrag)
        elif self.tool == "Path":
            #view.setCursor(Qt.BlankCursor)
            pass
        elif self.tool == "Rect":
            pass
        elif self.tool == "Poly":
            pass

    def set_tool_size(self, size):
        self.tool_size = size

    def event(self, event):
        super().event(event)

        if self.tool == "Path":
            if event.type() == QEvent.GraphicsSceneMousePress:
                self.gfx = PangoPathGraphic()

                self.gfx.setParentItem(self.label)
                self.gfx.set_width(self.tool_size)
                self.gfx.set_name("Rando Path")
                self.gfx.colorize()

                self.gfx.move_to(event.scenePos())
                return True
            if event.type() == QEvent.GraphicsSceneMouseMove:
                if self.gfx is not None:
                    self.gfx.line_to(event.scenePos())
                    return True
            if event.type() == QEvent.GraphicsSceneMouseRelease:
                if self.gfx is not None:
                    self.gfx = None
                    return True
        return False
 
class PangoGraphicsView(QGraphicsView):
    cursor_moved = pyqtSignal(QPoint)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setInteractive(True)
        self.setMouseTracking(True)

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

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        scene_pos = self.mapToScene(event.pos()).toPoint()
        self.cursor_moved.emit(scene_pos)
