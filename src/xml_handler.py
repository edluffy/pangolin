
import os.path
import xml.etree.cElementTree as ET
from xml.dom import minidom

from item import PangoLabelGraphic

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
        root_element = tree.getroot()

        for row in range(0, root_item.rowCount()):
            label_item = root_item.child(row)
            if label_item.hasChildren():
                for row in range(0, label_item.rowCount()):
                    shape_item = label_item.child(row)
                    shape_element = ET.SubElement(root_element, "Shape")
                    for prop in self.p_list:
                        if hasattr(shape_item, prop):
                            value = self.prop_to_str(shape_item, prop)
                            _ = ET.SubElement(shape_element, prop, attrib={'value':value})

        
        f = open(self.fname, "w")
        f.write(self.prettify(root_element))
        f.close()

    def prettify(self, elem):
        elem_str = ET.tostring(elem)
        return minidom.parseString(elem_str).toprettyxml(indent = "   ")

    def prop_to_str(self, item, prop):
        if prop == "color":
            p_str = getattr(item, prop).name()
        elif prop == "strokes":
            p_str = "["
            for pos, motion in getattr(item, prop):
                p_str += "(("+str(pos.x())+", "+str(pos.y())+"), "+motion+") "
            p_str += "["
        else:
            p_str = str(getattr(item, prop))
        return p_str
