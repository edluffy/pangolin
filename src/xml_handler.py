import re
import os.path
import xml.etree.cElementTree as ET
from xml.dom import minidom
from PyQt5.QtCore import QPointF

from PyQt5.QtGui import QColor

from item import PangoLabelGraphic, PangoLabelItem

class Xml_Handler():
    def __init__(self, fname, model):
        self.set_file(fname)
        self.model = model

        self.p_list = ["name", "fpath", "visible", 
                       "color", "icon", "width", 
                       "strokes", "points", "closed"]
        
    #TODO:
    #      Change file to write to depending on image folder open
    #      Figure out how to append to file or change element depending on scene
    #      Handle each variable individually

    def set_file(self, fname):
        self.fname = fname
        if not os.path.exists(fname):
            root = ET.Element('ProjectRoot')
            tree = ET.ElementTree(root)
            tree.write(open(self.fname, 'wb'))

    def write(self):
        tree = ET.parse(self.fname)
        root_item = self.model.invisibleRootItem()
        root_elem = tree.getroot()

        for row in range(0, root_item.rowCount()):
            label_item = root_item.child(row)
            label_elem = ET.SubElement(root_elem, "Label")
            self.copy_props_to_elem(label_item, label_elem)
            if label_item.hasChildren():
                for row in range(0, label_item.rowCount()):
                    shape_item = label_item.child(row)
                    shape_elem = ET.SubElement(label_elem, "Shape")
                    self.copy_props_to_elem(shape_item, shape_elem)
        
        f = open(self.fname, "w")
        f.write(self.prettify(root_elem))
        f.close()

    def read(self):
        tree = ET.parse(self.fname)
        root_item = self.model.invisibleRootItem()
        root_elem = tree.getroot()

        for label_elem in root_elem.iter("Label"):
            label_item = PangoLabelItem()
            self.copy_props_to_item(label_elem, label_item)
            root_item.appendRow(label_item)

            #for shape_elem in label_elem.iter("Shape"):
            #    shape_item = PangoLabelItem()
            #    self.copy_props_to_item(shape_elem, shape_item)
            #    root_item.appendRow(shape_item)


    def prettify(self, elem):
        elem_str = ET.tostring(elem)
        return minidom.parseString(elem_str).toprettyxml(indent = "   ")

    def copy_props_to_elem(self, item, elem):
        for p_type in self.p_list:
            if hasattr(item, p_type):
                p_str = self.prop_to_str(p_type, item)
                _ = ET.SubElement(elem, p_type, attrib={'value':p_str})

    def copy_props_to_item(self, shape_elem, item):
        for elem in shape_elem.iter():
            p_type = elem.tag
            p_str = elem.get('value')
            if hasattr(item, p_type):
                prop = self.str_to_prop(p_type, p_str)
                print(prop)
                setattr(item, p_type, prop)

    def prop_to_str(self, p_type, item):
        if p_type == "color":
            p_str = getattr(item, p_type).name()
        elif p_type == "strokes":
            p_str = "["
            for pos, motion in getattr(item, p_type):
                p_str += "("+str(pos.x())+" "+str(pos.y())+", "+motion+") "
            p_str += "]"
        else:
            p_str = str(getattr(item, p_type))
        return p_str
    
    def str_to_prop(self, p_type, p_str):
        if p_str=="None":
            return None
        if p_type == "visible":
            prop = bool(p_str)
        elif p_type == "color":
            prop = QColor(p_str)
        elif p_type == "width":
            prop = float(p_str)
        elif p_type == "strokes":
            prop = []
            for stroke in re.findall("\((.*?)\)", p_str):
                pos, motion = stroke.split(", ")
                x, y = pos.split(" ")
                prop.append((QPointF(x, y), motion))
        elif p_type == "closed":
            prop = bool(p_str)
        else:
            prop = p_str

        return prop

