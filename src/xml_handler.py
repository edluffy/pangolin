
from PyQt5.QtCore import QIODevice, QXmlStreamWriter

from item import PangoLabelGraphic

class Xml_Handler():
    def __init__(self, file, scene):
        self.file = file
        self.scene = scene

    #TODO: Change file to write to depending on image folder open
    #      Figure out how to append to file or change element depending on scene
    def write(self):
        self.file.open(QIODevice.ReadWrite)
        stream = QXmlStreamWriter(self.file)
        stream.setAutoFormatting(True)
        stream.writeStartDocument()

        for label in self.scene.items():
            if isinstance(label, PangoLabelGraphic):
                stream.writeStartElement("Label")
                for gfx in label.childItems():
                    stream.writeStartElement("Graphic")
                    for prop, v in gfx.props.items():
                        if prop == "color":
                            v_str = v.name()
                        elif prop == "strokes":
                            v_str = "["
                            for pos, motion in v:
                                v_str += "(("+str(pos.x())+", "+str(pos.y())+"), "+motion+") "
                            v_str += "["
                        else:
                            v_str = str(v)
                        stream.writeTextElement(prop, v_str)
                    stream.writeEndElement() # Child
                stream.writeEndElement() # Label

        stream.writeEndDocument()
        self.file.close()

    def read(self):
        pass

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

