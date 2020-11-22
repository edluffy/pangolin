import os

from item import PangoBboxItem

def yolo_write(interface, items, fpath):
    pre, ext = os.path.splitext(fpath)
    print(pre+".txt")
    with open(pre+".txt", 'w') as f:
        for item in items:
            if type(item) == PangoBboxItem:
                rect = item.rect
            else:
                rect = interface.map[item.key()].boundingRect()
                rect = rect.intersected(interface.map[item.parent().key()].boundingRect())

            f.write("%d %.6f %.6f %.6f %.6f\n" % (item.parent().row(),
                rect.center().x(), rect.center().y(), 
                rect.width(), rect.height()))
