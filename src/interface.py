from PyQt5.QtCore import QItemSelectionModel, QModelIndex, QPersistentModelIndex, Qt
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QGraphicsItem

from bidict import bidict
from graphics import PangoGraphicsScene

from item import PangoGraphic, PangoItem, PangoLabelGraphic, PangoLabelItem, PangoPathGraphic, PangoPathItem, PangoPolyGraphic, PangoPolyItem, PangoRectGraphic, PangoRectItem
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

    def filter_tree(self, fpath=None):
        self.fpath = fpath
        root_item = self.model.invisibleRootItem()

        # Filtering labels
        for i in range(0, root_item.rowCount()):
            label_item = root_item.child(i)
            label_gfx = self.map[label_item.key()]

            if label_item.fpath==self.fpath:
                self.tree.setRowHidden(i, root_item, False)
                if label_gfx.scene() is not self.scene:
                    self.scene.addItem(label_gfx)
            else:
                self.tree.setRowHidden(i, label_item.index(), True)
                if label_gfx.scene() is self.scene:
                    self.scene.removeItem(label_gfx)

            # Filtering shapes
            for j in range(0, label_item.rowCount()):
                shape_item = label_item.child(j)
                shape_gfx = self.map[shape_item.key()]

                if label_item.fpath==self.fpath:
                    self.tree.setRowHidden(j, shape_item.index(), False)
                    if shape_gfx.scene() is not self.scene:
                        self.scene.addItem(shape_gfx)
                else:
                    self.tree.setRowHidden(j, shape_item.index(), True)
                    if shape_gfx.scene() is self.scene:
                        self.scene.removeItem(shape_gfx)
    
    def item_selection_changed(self):
        new = [self.map[QPersistentModelIndex(idx)] for idx in self.tree.selectedIndexes()]
        old = self.scene.selectedItems()

        for gfx in set(new)-set(old):
            gfx.setSelected(True)

        for gfx in set(old)-set(new):
            gfx.setSelected(False)

    def gfx_selection_changed(self):
        new = [QModelIndex(self.map.inverse[gfx]) for gfx in self.scene.selectedItems()]
        old = self.tree.selectedIndexes()

        for idx in set(new)-set(old):
            self.tree.selectionModel().select(idx, QItemSelectionModel.Select)

        for idx in set(old)-set(new):
            self.tree.selectionModel().select(idx, QItemSelectionModel.Deselect)

    def item_changed(self, top_idx, bottom_idx, roles):
        item = self.model.itemFromIndex(top_idx)
        try:
            gfx = self.map[item.key()]
        except KeyError:
            gfx = self.create_gfx_from_item(item)

        #for role in roles:
            #print("Item change: ", pango_item_role_debug(role))
            #if role == Qt.DisplayRole:
            #    gfx.name = item.name
            #elif role == Qt.CheckStateRole:
            #    gfx.visible = item.visible
            #elif role == Qt.DecorationRole:
            #    if hasattr(gfx, "color"):
            #        gfx.color = item.color

            # Sync properties 
            for prop, value in item.__dict__.items():
                print(prop)
                if value is not None and value != []:
                    if value != getattr(gfx, prop):
                        setattr(gfx, prop, value)

    def gfx_changed(self, gfx, change):
        #print("Gfx change: ", pango_gfx_change_debug(change))
        try:
            item = self.model.itemFromIndex(QModelIndex(self.map.inverse[gfx]))
        except KeyError:
            item = self.create_item_from_gfx(gfx)

        #if change == QGraphicsItem.ItemToolTipHasChanged:
        #    item.name = gfx.name
        #elif change == QGraphicsItem.ItemVisibleHasChanged:
        #    item.visible = gfx.visible

        # Sync properties 
        for prop, value in gfx.__dict__.items():
            if value is not None and value != []:
                if value != getattr(item, prop):
                    setattr(item, prop, value)

    def item_removed(self, parent_idx, first, last):
        if parent_idx.isValid():
            item = self.model.itemFromIndex(parent_idx).child(first, 0)
        else:
            item = self.model.item(first, 0)

        gfx = self.map[item.key()]
        _ = self.map.pop(item.key())
        del gfx

    def gfx_removed(self, gfx):
        idx = QModelIndex(self.map.inverse[gfx])
        self.model.removeRow(idx.row(), idx.parent())

    #TODO: Use reflection here
    def create_item_from_gfx(self, gfx):
        if type(gfx) is PangoLabelGraphic:
            item = PangoLabelItem()
        elif type(gfx) is PangoPathGraphic:
            item = PangoPathItem()
        elif type(gfx) is PangoPolyGraphic:
            item = PangoPolyItem()
        elif type(gfx) is PangoRectGraphic:
            item = PangoRectItem()
        else:
            item = PangoItem()

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
        if type(item) is PangoLabelItem:
            gfx = PangoLabelGraphic()
        elif type(item) is PangoPathItem:
            gfx = PangoPathGraphic()
        elif type(item) is PangoPolyItem:
            gfx = PangoPolyGraphic()
        elif type(item) is PangoRectItem:
            gfx = PangoRectGraphic()
        else:
            gfx = PangoGraphic()

        # Map, then add to scene
        self.map[item.key()] = gfx
        if item.parent() is not None:
            gfx.setParentItem(self.map[item.parent().key()])
        else:
            self.scene.addItem(gfx)
        return gfx
    
