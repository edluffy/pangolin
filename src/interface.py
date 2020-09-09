from PyQt5.QtCore import (QItemSelectionModel, QModelIndex,
                          QPersistentModelIndex, Qt)
from PyQt5.QtWidgets import QGraphicsItem

from bidict import bidict

from item import PangoGraphic, PangoItem, PangoLabelGraphic, PangoLabelItem, PangoPathGraphic, PangoPathItem, PangoPolyGraphic, PangoPolyItem, PangoRectGraphic, PangoRectItem
from utils import PangoShapeType, pango_gfx_change_debug, pango_item_role_debug

""" PangoModelSceneInterface promotes loose coupling by keeping model/view and 
   scene/view from referring to each other explicitly """
class PangoModelSceneInterface(object):
    def __init__(self):
        super().__init__()
        self.map = bidict()

    # Model/View changes (item) ----> Scene/View (gfx)
    def set_model(self, model, view):
        self.model = model
        self.model.dataChanged.connect(self.item_changed)
        self.model.rowsAboutToBeRemoved.connect(self.item_removed)

        self.view = view
        self.view.selectionModel().selectionChanged.connect(self.item_selection_changed)

    # Scene/View changes (gfx) ----> Model/View (item)
    def set_scene(self, scene):
        self.scene = scene
        self.scene.gfx_changed.connect(self.gfx_changed)
        self.scene.gfx_removed.connect(self.gfx_removed)
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
        try:
            gfx = self.map[item.key()]
        except KeyError:
            gfx = self.create_gfx_from_item(item)

        for role in roles:
            #print("Item change: ", pango_item_role_debug(role))
            if role == Qt.DisplayRole:
                gfx.set_name(item.name())
            elif role == Qt.DecorationRole:
                gfx.set_decoration(item.decoration())
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
            item.set_decoration(gfx.decoration())
        elif change == QGraphicsItem.ItemVisibleHasChanged:
            item.set_visible(gfx.visible())

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
            parent_item = self.model.itemFromIndex(QModelIndex(self.map.inverse[gfx.parentItem()]))
            parent_item.appendRow(item)
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

    def set_label(self, row):
        item = self.model.item(row)
        try:
            self.scene.set_label(self.map[item.key()])
        except:
            return


