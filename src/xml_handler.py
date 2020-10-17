import re
import os.path
import xml.etree.cElementTree as ET
from xml.dom import minidom
from PyQt5.QtCore import QPointF

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMessageBox

from item import PangoLabelGraphic, PangoLabelItem, PangoPathItem, PangoPolyItem, PangoRectItem

class Xml_Handler():
    def __init__(self, model):
        self.model = model

        self.p_list = ["name", "fpath", "visible", 
                       "color", "icon", "width", 
                       "strokes", "points", "closed"]
        
    #TODO: properly serialize polygon tool
    #      add load file dialog
          
    def check_file(self, fname):
        if os.path.exists(fname):
            dialog = QMessageBox()
            dialog.setText("Pango project file exists, overwrite?")
            dialog.setInformativeText("Located at: "+fname)
            dialog.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            dialog.setDefaultButton(QMessageBox.Save)

            if dialog.exec() == QMessageBox.Cancel:
                return False

        return True
    
    def load_file(self):
        pass
        # add dialog here

    def write(self, fname):
        if not self.check_file(fname):
            return

        root_item = self.model.invisibleRootItem()
        root_elem = ET.Element('InvisibleRootItem')

        for row in range(0, root_item.rowCount()):
            label_item = root_item.child(row)
            label_elem = ET.SubElement(root_elem, type(label_item).__name__)
            self.copy_props_to_elem(label_item, label_elem)
            if label_item.hasChildren():
                for row in range(0, label_item.rowCount()):
                    shape_item = label_item.child(row)
                    shape_elem = ET.SubElement(label_elem, type(shape_item).__name__)
                    self.copy_props_to_elem(shape_item, shape_elem)
        
        f = open(fname, "w")
        f.write(self.prettify(root_elem))
        f.close()

    def copy_props_to_elem(self, item, elem):
        for p_type in self.p_list:
            if hasattr(item, p_type):
                p_str = self.prop_to_str(p_type, item)
                _ = ET.SubElement(elem, p_type, attrib={'value':p_str})

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

    def read(self, fname):
        tree = ET.parse(fname)
        root_item = self.model.invisibleRootItem()
        root_elem = tree.getroot()

        for label_elem in root_elem:
            label_item = PangoLabelItem()
            root_item.appendRow(label_item)
            self.copy_props_to_item(label_elem, label_item)

            for shape_elem in label_elem:
                if shape_elem.tag.startswith("Pango"):
                    try:
                        shape_item = globals()[shape_elem.tag]()
                    except KeyError:
                        print("Read error - unknown item type", shape_elem.tag)
                        return
                    label_item.appendRow(shape_item)
                    self.copy_props_to_item(shape_elem, shape_item)

    def copy_props_to_item(self, p_elem, item):
        for elem in p_elem:
            p_type = elem.tag
            p_str = elem.get('value')
            if p_str is not None and hasattr(item, p_type):
                prop = self.str_to_prop(p_type, p_str)
                setattr(item, p_type, prop)

        item.decorate() # Mostly for triggering refresh
    
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
                prop.append((QPointF(float(x), float(y)), motion))
        elif p_type == "closed":
            prop = bool(p_str)
        else:
            prop = p_str

        return prop

    def prettify(self, elem):
        elem_str = ET.tostring(elem)
        return minidom.parseString(elem_str).toprettyxml(indent = "   ")

