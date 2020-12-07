import os
from PyQt5.QtCore import QModelIndex
from PyQt5.QtGui import QImage
from lxml import etree

from item import PangoBboxItem, PangoLabelItem, PangoPathItem, PangoPolyItem
from utils import pango_get_icon, pango_get_palette

def pascal_voc_write(interface, fpath):
    items = []
    for k in interface.map.keys():
        item = interface.model.itemFromIndex(QModelIndex(k))
        if hasattr(item, "fpath") and item.fpath == fpath:
            items.append(item)
    if items == []:
        return

    img = QImage(fpath)
    root = etree.Element("annotation")

    etree.SubElement(root, "folder").text = os.path.basename(os.path.dirname(fpath))
    etree.SubElement(root, "filename").text = os.path.basename(fpath)
    etree.SubElement(root, "path").text = fpath

    source = etree.SubElement(root, "source")
    etree.SubElement(source, "database").text = "Unknown"

    size = etree.SubElement(root, "size")
    etree.SubElement(size, "width").text = str(img.width())
    etree.SubElement(size, "height").text = str(img.height())
    etree.SubElement(size, "depth").text = str((3, 1)[img.isGrayscale()])

    etree.SubElement(root, "segmented").text = "0"

    for item in items:
        if type(item) == PangoBboxItem:
            rect = item.rect
        elif type(item) in (PangoPolyItem, PangoPathItem):
            rect = interface.map[item.key()].boundingRect()
            rect = rect.intersected(interface.map[item.parent().key()].boundingRect())
        else:
            continue
            
        object = etree.SubElement(root, "object")
        etree.SubElement(object, "name").text = item.parent().name
        etree.SubElement(object, "pose").text = "Unspecified"
        etree.SubElement(object, "truncated").text = "0"
        etree.SubElement(object, "difficult").text = "0"

        bndbox = etree.SubElement(object, "bndbox")
        etree.SubElement(bndbox, "xmin").text = str(round(rect.left()))
        etree.SubElement(bndbox, "xmax").text = str(round(rect.right()))
        etree.SubElement(bndbox, "ymin").text = str(round(rect.top()))
        etree.SubElement(bndbox, "ymax").text = str(round(rect.bottom()))

    tree = etree.ElementTree(root)
    pre, ext = os.path.splitext(fpath)
    with open(pre+".xml", 'wb') as f:
        tree.write(f, encoding="utf-8", xml_declaration=True, pretty_print=True)

def pascal_voc_read(interface, fpath):
    tree = etree.parse(fpath)
    root = tree.getroot()

    pre, ext = os.path.splitext(fpath)
    if os.path.exists(pre+".png"):
        img_fpath = pre+".png"
    elif os.path.exists(pre+".jpg"):
        img_fpath = pre+".jpg"
    else:
        return

    for object in root.iterfind("object"):
        name = object.find("name")
        # Create shape
        shape = PangoBboxItem()
        shape.visible = True
        shape.fpath = img_fpath

        for k in interface.map.keys():
            label = interface.model.itemFromIndex(QModelIndex(k))
            if label.name == name.text:
                label.appendRow(shape)
                break

        if shape.parent() is None: # Create Label if not found
            label = PangoLabelItem()
            interface.model.invisibleRootItem().appendRow(label)

            label.name = name.text
            label.visible = True
            label.color = pango_get_palette(label.row())
            label.set_icon()

            label.appendRow(shape)

        bndbox = object.find("bndbox")
        shape.rect.setLeft(float(bndbox.findtext("xmin")))
        shape.rect.setRight(float(bndbox.findtext("xmax")))
        shape.rect.setTop(float(bndbox.findtext("ymin")))
        shape.rect.setBottom(float(bndbox.findtext("ymax")))

        shape.name = "Bbox at "+ "("+str(round(shape.rect.topLeft().x()))\
              +", "+str(round(shape.rect.topLeft().y()))+")"
        shape.set_icon()



