from PyQt5.QtCore import QItemSelectionModel, QModelIndex, QPersistentModelIndex, Qt
from PyQt5.QtGui import QColor, QStandardItemModel
from PyQt5.QtWidgets import QGraphicsItem

from bidict import bidict
from graphics import PangoGraphicsScene

from item import PangoGraphic, PangoItem, PangoLabelGraphic, PangoLabelItem, PangoPathGraphic, PangoPathItem, PangoPolyGraphic, PangoPolyItem, PangoBboxGraphic, PangoBboxItem
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
        old = [item.key() for item in self.find_in_tree("fpath", old_fpath, 1, True)]
        new = [item.key() for item in self.find_in_tree("fpath", new_fpath, 1, True)]

        for key in new:
            item = self.model.itemFromIndex(QModelIndex(key))
            gfx = self.map[key]

            if item.parent() is None:
                self.tree.setRowHidden(item.row(), QModelIndex(), False)
            else:
                self.tree.setRowHidden(item.row(), item.parent().index(), False)

            if gfx.scene() is not self.scene:
                self.scene.addItem(gfx)

        for key in old:
            item = self.model.itemFromIndex(QModelIndex(key))
            gfx = self.map[key]

            if item.parent() is None:
                self.tree.setRowHidden(item.row(), QModelIndex(), True)
            else:
                self.tree.setRowHidden(item.row(), item.parent().index(), True)

            if gfx.scene() is self.scene:
                self.scene.removeItem(gfx)

    def copy_labels_tree(self, new_fpath, old_fpath):
        old = [item.name for item in self.find_in_tree("fpath", old_fpath, 1)]
        new = [item.name for item in self.find_in_tree("fpath", new_fpath, 1)]

        for name in set(old)-set(new):
            ms = self.find_in_tree("name", name, 1)
            if ms is not None:
                label = ms[0]
                dupe_label = globals()[type(label).__name__]()
                self.model.appendRow(dupe_label)

                dupe_label.setattrs(**label.getattrs())
                dupe_label.fpath = new_fpath
                dupe_label.set_icon()

    def del_labels_tree(self):
        i_model = self.interface.model

    def find_in_tree(self, prop, value, levels=2, inclusive=False):
        matches = []
        root = self.model.invisibleRootItem()
        if levels > 0: # (Labels)
            for i in range(0, root.rowCount()):
                item = root.child(i)
                if getattr(item, prop) == value:
                    matches.append(item)
                    if inclusive:
                        matches.extend(item.children())
                if levels > 1: # (Shapes)
                    for i in range(0, item.rowCount()):
                        item_child = item.child(i)
                        if getattr(item_child, prop) == value:
                            matches.append(item_child)
                            if inclusive:
                                matches.extend(item_child.children())
        return matches
    
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
        item = self.model.itemFromIndex(top_idx)
        #print("Item change: ", pango_item_role_debug(roles[0]))
        try:
            gfx = self.map[item.key()]
        except KeyError:
            gfx = self.create_gfx_from_item(item)

        # Sync properties 
        for k, v in item.getattrs().items():
            if not(v is None or v==[] or v=="" or (type(v) is QColor and v==QColor())):
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
            if not(v is None or v==[] or v=="" or v==0 or (type(v) is QColor and v==QColor())):
                setattr(item, k, v)

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
        else:
            self.scene.addItem(gfx)
        return gfx
    
