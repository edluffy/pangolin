from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap
from PyQt5.QtWidgets import (QApplication, QGraphicsPathItem, QGraphicsScene,
                             QGraphicsView, QHBoxLayout, QLabel, QMainWindow)

app = QApplication([])

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Hello world")
        self.setGeometry(50, 50, 1500, 800)

        self.canvas = Canvas()
        self.view = QGraphicsView(self.canvas)

        self.setCentralWidget(self.view)

class Canvas(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Dummy data
        self.tool = "Brush"
        self.color = QColor('green')
        self.visible = True

    def get_pen(self):
        pen = QPen()
        pen.setWidth(10)
        pen.setCapStyle(Qt.RoundCap)
        pen.setColor(QColor("green"))
        return pen


    def mousePressEvent(self, event):
        self.current_item = QGraphicsPathItem()
        self.addItem(self.current_item)

        self.current_item.setPen(self.get_pen())
        self.current_item.setOpacity(0.2)

        if self.tool == "Brush":
            path = QPainterPath(event.scenePos())
            self.current_item.setPath(path)

    def mouseMoveEvent(self, event):
        if self.tool == "Brush" and self.current_item is not None:
            path = self.current_item.path()
            path.lineTo(event.scenePos())
            self.current_item.setPath(path)

    def mouseReleaseEvent(self, event):
        if self.tool == "Brush" and self.current_item is not None:
            self.current_item.setOpacity(0.4)
            self.current_item = None
window = MainWindow()
window.show()

app.exec_()
