import os
from PyQt5.QtGui import QImage
from lxml import etree

def pascal_voc_write(items, fpath):
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
        object = etree.SubElement(root, "object")
        etree.SubElement(object, "name").text = item.parent().name
        etree.SubElement(object, "pose").text = "Unspecified"
        etree.SubElement(object, "truncated").text = "0"
        etree.SubElement(object, "difficult").text = "0"

        bndbox = etree.SubElement(object, "bndbox")
        etree.SubElement(bndbox, "xmin").text = str(item.rect.left())
        etree.SubElement(bndbox, "xmax").text = str(item.rect.right())
        etree.SubElement(bndbox, "ymin").text = str(item.rect.top())
        etree.SubElement(bndbox, "ymax").text = str(item.rect.bottom())

    txt = etree.tostring(root, pretty_print=True)
    print(txt.decode("utf-8"))
