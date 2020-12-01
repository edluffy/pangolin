import os

from PyQt5.QtCore import QPointF
from src.utils import pango_get_palette
from src.item import PangoLabelItem
from item import PangoBboxItem, PangoPathItem, PangoPolyItem

def yolo_write(interface, fpath, items):
    pre, ext = os.path.splitext(fpath)
    with open(pre+".txt", 'w') as f:
        for item in items:
            if type(item) == PangoBboxItem:
                rect = item.rect
            elif type(item) in (PangoPolyItem, PangoPathItem):
                rect = interface.map[item.key()].boundingRect()
                rect = rect.intersected(interface.map[item.parent().key()].boundingRect())
            else:
                continue

            f.write("%d %.6f %.6f %.6f %.6f\n" % (item.parent().row(),
                rect.center().x(), rect.center().y(), 
                rect.width(), rect.height()))

def yolo_read(interface, fpath):
    pre, ext = os.path.splitext(fpath)
    if os.path.exists(pre+".png"):
        img_fpath = pre+".png"
    elif os.path.exists(pre+".jpg"):
        img_fpath = pre+".jpg"
    else:
        return

    with open(fpath, 'r') as f:
        lines = f.readlines()
        print(lines)
        for line in lines:
            row, cx, cy, w, h = map(float, line.split(" "))

            # Create Label if not present
            if interface.model.item(int(row)) is None:
                label = PangoLabelItem()
                interface.model.invisibleRootItem().appendRow(label)

                label.name = "Unnamed Label "+str(label.unique_row())
                label.visible = True
                label.fpath = img_fpath
                label.color = pango_get_palette(label.unique_row()-1)
                label.set_icon()
            
            # Create shape
            shape = PangoBboxItem()
            interface.model.item(row).appendRow(shape)

            shape.visible = True
            shape.fpath = img_fpath
            shape.rect.setWidth(w)
            shape.rect.setHeight(h)
            shape.rect.moveCenter(QPointF(cx, cy))

            shape.name = "Bbox at "+ "("+str(round(shape.rect.topLeft().x()))\
                  +", "+str(round(shape.rect.topLeft().y()))+")"
            shape.set_icon()
