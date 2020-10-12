
import os.path
import xml.etree.cElementTree as ET
from xml.dom import minidom

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
            label_item.setattrs()
            for p_name, p_str in label_elem.attrib:
                setattr(label_item, p_name, self.str_to_prop(label_item, p_str))
            root_item.appendRow(label_item)


    def prettify(self, elem):
        elem_str = ET.tostring(elem)
        return minidom.parseString(elem_str).toprettyxml(indent = "   ")

    def copy_props_to_elem(self, item, elem):
        for p_name in self.p_list:
            if hasattr(item, p_name):
                p_str = self.prop_to_str(item, p_name)
                _ = ET.SubElement(elem, p_name, attrib={'value':p_str})

    def copy_props_to_item(self, elem, item):
        for p_name, p_str in elem.attrib:
            if hasattr(item, p_name):
                value = self.str_to_prop(p_name, p_str)

    def prop_to_str(self, item, p_name):
        if p_name == "color":
            p_str = getattr(item, p_name).name()
        elif p_name == "strokes":
            p_str = "["
            for pos, motion in getattr(item, p_name):
                p_str += "(("+str(pos.x())+", "+str(pos.y())+"), "+motion+") "
            p_str += "["
        else:
            p_str = str(getattr(item, p_name))
        return p_str
    
    #TODO: Handle each variable individually
    def str_to_prop(self, p_name, p_str):
        if p_name == "visible":
            prop = bool(p_str)
        elif p_name == "color":
            prop = QColor(p_str)
        elif p_name == "width":
            prop = float(p_str)
        elif p_name == "strokes":
            pass
        elif p_name == "points":
            pass
        elif p_name == "closed":
            pass
        else:
            prop = p_str

