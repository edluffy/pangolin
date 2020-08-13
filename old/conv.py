import math
from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap, QPainter, QImage, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QHBoxLayout

COLORS = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
          '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe',
          '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000',
          '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080']

GRAYSCALE = []
app = QApplication([])

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Hello world")
        self.setGeometry(50, 50, 1500, 800)

        img = QImage('/Users/edluffy/Downloads/Label_1.png')
        print(img.format())

        bg = QLabel()
        self.setCentralWidget(bg)
        layout = QHBoxLayout()
        bg.setLayout(layout)
        

        # The image is stored using an 8-bit grayscale format
        pxs = []
        for _ in range(0, 10):
            px = img2px(img)
            img = px2img(px)
            pxs.append(img2px(img))

        #newpx = QPixmap().fromImage(toFile(px))

        for px in pxs[-3:]:
            lbl = QLabel(self)
            px = px.scaledToWidth(self.width()/3)
            lbl.setPixmap(px)
            layout.addWidget(lbl)

def img2px(img):
    layers = []
    px = QPixmap().fromImage(img)
    for i, color in enumerate(COLORS, 0):
        tmp = QPixmap(px.size())
        tmp.fill(QColor(int(color[1:], 16)))
        tmp.setMask(px.createMaskFromColor(QColor.fromRgb(i, i, i), QtCore.Qt.MaskOutColor))
        layers.append(tmp)
    return quickOverlay(layers, [1 for _ in layers])

def px2img(px):
    layers=[]
    for i, color in enumerate(COLORS, 0):
        tmp = QPixmap(px.size())
        tmp.fill(QColor.fromRgb(i, i, i))
        tmp.setMask(px.createMaskFromColor(QColor(int(color[1:], 16)), QtCore.Qt.MaskOutColor))
        layers.append(tmp)
    px = quickOverlay(layers, [1 for _ in layers])
    return px.toImage().convertToFormat(QImage.Format_Grayscale8)

def quickOverlay(layers, opacities=[]):
    res = QPixmap(layers[0].size())
    qp = QPainter(res)
    for layer, op in zip(layers, opacities):
        qp.setOpacity(op)
        qp.drawPixmap(QtCore.QPoint(0, 0), layer)
    return res

def argbtoi(argb):
    return (argb[0] << 24) + (argb[1]<<16) + (argb[2]<<8) + argb[3]

window = MainWindow()
window.show()

app.exec_()
