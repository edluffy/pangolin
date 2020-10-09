
import os.path
import xml.etree.cElementTree as ET

from item import PangoLabelGraphic

class Xml_Handler():
    def __init__(self, fname, scene):
        self.set_file(fname)
        self.scene = scene

    #TODO: Pretty print xml output
    #      Change file to write to depending on image folder open
    #      Figure out how to append to file or change element depending on scene

    def set_file(self, fname):
        self.fname = fname
        if not os.path.exists(fname):
            root = ET.Element('ProjectRoot')
            tree = ET.ElementTree(root)
            tree.write(open(self.fname, 'wb'))

    def write(self):
        for label in self.scene.items():
            if isinstance(label, PangoLabelGraphic):
                for gfx in label.childItems():
                    for k, v in gfx.__dict__.items():
                        if k.startswith("_"):
                            print(k)

        #tree = ET.parse(self.fname)
        #root = tree.getroot()
        #for label in self.scene.items():
        #    print("got here")
        #    if isinstance(label, PangoLabelGraphic):
        #        label_element = ET.SubElement(root, "Label")
        #        for gfx in label.childItems():
        #            gfx_element = ET.SubElement(label_element, "Graphic")
        #            for prop, v in gfx.props.items():
        #                _ = ET.SubElement(gfx_element, self.get_text(prop, v))
        #tree.write(open(self.fname, 'wb'))

    def read(self):
        pass

    def get_text(self, prop, v):
        if prop == "color":
            v_str = v.name()
        elif prop == "strokes":
            v_str = "["
            for pos, motion in v:
                v_str += "(("+str(pos.x())+", "+str(pos.y())+"), "+motion+") "
            v_str += "["
        else:
            v_str = str(v)
        return v_str

        #root = self.interface.model.invisibleRootItem()
        #stream.writeStartElement("root")
        #for row in range(0, root.rowCount()):
        #    label = root.child(row)
        #    if label.hasChildren():
        #        stream.writeStartElement(label.name)
        #        for row in range(0, label.rowCount()):
        #            shape = label.child(row)
        #            gfx = self.interface.map[shape.key()]
        #            print(gfx.props)
        #            stream.writeStartElement(shape.name)
        #            stream.writeAttribute("fpath", shape.fpath)
        #            stream.writeEndElement() # Shape
        #        stream.writeEndElement() # Label
        #stream.writeEndElement() # Root

