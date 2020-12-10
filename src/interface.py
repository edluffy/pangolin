from PyQt5.QtCore import QItemSelectionModel, QModelIndex, QPersistentModelIndex, QRectF, Qt
from PyQt5.QtGui import QColor, QStandardItemModel
from PyQt5.QtWidgets import QGraphicsItem

from bidict import bidict
from graphics import PangoGraphicsScene

from item import PainterPath, PangoGraphic, PangoItem, PangoLabelGraphic, PangoLabelItem, PangoPathGraphic, PangoPathItem, PangoPolyGraphic, PangoPolyItem, PangoBboxGraphic, PangoBboxItem, PolygonF
from utils import pango_gfx_change_debug, pango_item_role_debug

""" PangoModelSceneInterface promotes loose coupling by keeping model/view and 
   scene/view from referring to each other explicitly """
class PangoModelSceneInterface(object):
    def __init__(self):
        super().__init__()
        self.map = bidict()

        # Model/View changes (item) ----> Scene/View (gfx)
        self.model = QStandardItemModel()
        self.model.dataChanged.connect(self.item_changed)
        self.model.rowsAboutToBeRemoved.connect(self.item_removed)

        # Scene/View changes (gfx) ----> Model/View (item)
        self.scene = PangoGraphicsScene()
        self.scene.gfx_changed.connect(self.gfx_changed)
        self.scene.gfx_removed.connect(self.gfx_removed)
        self.scene.selectionChanged.connect(self.gfx_selection_changed)

    def set_tree(self, view):
        self.tree = view
        if self.tree.selectionModel() is not None:
            self.tree.selectionModel().selectionChanged.connect(self.item_selection_changed)

    def filter_tree(self, new_fpath, old_fpath):
        for key, gfx in self.map.items():
            item = self.model.itemFromIndex(QModelIndex(key))
            if hasattr(item, "fpath"): # ( = not a label)
                if item.fpath == new_fpath:
                    self.tree.setRowHidden(item.row(), item.parent().index(), False)
                    if gfx.scene() is None:
                        self.scene.addItem(gfx)
                        gfx.setParentItem(self.map[item.parent().key()])
                        gfx.inherit_color() # incase color has changed
                else:
                    self.tree.setRowHidden(item.row(), item.parent().index(), True)
                    if gfx.scene() is not None:
                        self.scene.removeItem(gfx)

    def switch_label(self, row):
        item = self.model.item(row)
        if item is not None:
            try:
                self.scene.active_label = self.map[item.key()]
            except KeyError:
                return

            self.scene.reticle.setBrush(self.scene.active_label.color)
            self.scene.reset_com()

    def del_labels(self, row):
        if self.model.rowCount() > 0:
            gfxs = []
            item = self.model.item(row)
            for i in range(0, item.rowCount()):
                gfxs.append(self.map[item.child(i).key()])

            self.scene.unravel_shapes(*gfxs)
            idx = item.index()
            self.model.removeRow(idx.row(), idx.parent())
            self.model.removeRow(idx.row(), idx.parent()) # Twice is necessary
            self.filter_tree(self.scene.fpath, None)

    def item_selection_changed(self):
        try:
            new = [self.map[QPersistentModelIndex(idx)] for idx in self.tree.selectedIndexes()]
        except KeyError:
            return
        old = self.scene.selectedItems()

        for gfx in set(new)-set(old):
            gfx.setSelected(True)

        for gfx in set(old)-set(new):
            gfx.setSelected(False)

    def gfx_selection_changed(self):
        try:
            new = [QModelIndex(self.map.inverse[gfx]) for gfx in self.scene.selectedItems()]
        except KeyError:
            return
        old = self.tree.selectedIndexes()

        for idx in set(new)-set(old):
            self.tree.selectionModel().select(idx, QItemSelectionModel.Select)

        for idx in set(old)-set(new):
            self.tree.selectionModel().select(idx, QItemSelectionModel.Deselect)

    def item_changed(self, top_idx, bottom_idx, roles):
        if roles is None:
            return
        item = self.model.itemFromIndex(top_idx)
        #print("Item change: ", pango_item_role_debug(roles[0]))

        try:
            gfx = self.map[item.key()]
        except KeyError:
            gfx = self.create_gfx_from_item(item)

        # Sync properties 
        for k, v in item.getattrs().items():
            if not self.var_empty(v):
                setattr(gfx, k, v)


    def gfx_changed(self, gfx, change):
        #print("Gfx change: ", pango_gfx_change_debug(change))
        try:
            item = self.model.itemFromIndex(QModelIndex(self.map.inverse[gfx]))
        except KeyError:
            item = self.create_item_from_gfx(gfx)
            item.set_icon()

        # Sync properties 
        for k, v in gfx.getattrs().items():
            if k == "visible" or k == "color":
                continue # Glitch fix
            if not self.var_empty(v):
                setattr(item, k, v)

    def var_empty(self, v):
        return v is None or v==[] or v=="" or v==0\
                or (type(v) is QColor and v==QColor())\
                or (type(v) is PainterPath and v==PainterPath())\
                or (type(v) is PolygonF and v==PolygonF())\
                or (type(v) is QRectF and v==QRectF())

    def item_removed(self, parent_idx, first, last):
        if parent_idx.isValid():
            item = self.model.itemFromIndex(parent_idx).child(first, 0)
        else:
            item = self.model.item(first, 0)

        gfx = self.map[item.key()]
        _ = self.map.pop(item.key())
        if gfx.scene() is not None:
            gfx.scene().removeItem(gfx)
        del gfx

    def gfx_removed(self, gfx):
        idx = QModelIndex(self.map.inverse[gfx])
        self.model.removeRow(idx.row(), idx.parent())

    def create_item_from_gfx(self, gfx):
        class_name = type(gfx).__name__.replace("Graphic", "Item")
        item = globals()[class_name]()

        # Add to model, then map
        if gfx.parentItem() is not None:
            parent_item = self.model.itemFromIndex(
                    QModelIndex(self.map.inverse[gfx.parentItem()]))
            parent_item.appendRow(item)
            self.tree.expand(parent_item.index())
        else:
            self.model.appendRow(item)
        self.map[item.key()] = gfx
        return item

    def create_gfx_from_item(self, item):
        class_name = type(item).__name__.replace("Item", "Graphic")
        gfx = globals()[class_name]()

        # Map, then add to scene
        self.map[item.key()] = gfx
        if item.parent() is not None:
            gfx.setParentItem(self.map[item.parent().key()])
            gfx.inherit_color()
        else:
            self.scene.addItem(gfx)
        return gfx
    
