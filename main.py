import os

from PyQt5 import QtCore
from PyQt5.QtGui import (QBrush, QColor, QFont, QIcon, QImage, QKeySequence,
                         QPainter, QPen, QPixmap, QPolygonF)
from PyQt5.QtWidgets import (QAction, QActionGroup, QApplication,
                             QDialogButtonBox, QFileDialog, QGraphicsScene,
                             QGraphicsView, QHBoxLayout, QLabel, QListWidget,
                             QListWidgetItem, QMainWindow, QMessageBox,
                             QShortcut, QStackedLayout, QToolBar,
                             QWidgetAction, QVBoxLayout, QPushButton, QStyle)

MAX_CODES = 20
COLORS = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
          '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe',
          '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000',
          '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080']

app = QApplication([])

global toMaskPath
def toMaskPath(path):
    fn = "M_"+os.path.basename(os.path.splitext(path)[0]+".png")
    return os.path.join(os.path.dirname(path), "Masks", fn)

global img2px
def img2px(img):
    layers = []
    px = QPixmap().fromImage(img)
    for i, color in enumerate(COLORS, 0):
        tmp = QPixmap(px.size())
        tmp.fill(QColor(int(color[1:], 16)))
        tmp.setMask(px.createMaskFromColor(QColor.fromRgb(i, i, i), QtCore.Qt.MaskOutColor))
        layers.append(tmp)
    return quickOverlay(layers, [1 for _ in layers])

global px2img
def px2img(px):
    layers=[]
    for i, color in enumerate(COLORS, 0):
        tmp = QPixmap(px.size())
        tmp.fill(QColor.fromRgb(i, i, i))
        tmp.setMask(px.createMaskFromColor(QColor(int(color[1:], 16)), QtCore.Qt.MaskOutColor))
        layers.append(tmp)
    px = quickOverlay(layers, [1 for _ in layers])
    return px.toImage().convertToFormat(QImage.Format_Grayscale8)

global quickOverlay
def quickOverlay(layers, opacities=[]):
    res = QPixmap(layers[0].size())
    qp = QPainter(res)
    for layer, op in zip(layers, opacities):
        qp.setOpacity(op)
        qp.drawPixmap(QtCore.QPoint(0, 0), layer)
    return res

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)


        self.setWindowTitle("KitPainter")
        self.setGeometry(50, 50, 1000, 600)
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.initKeys()

        self.menubar = MenuBar("Menu Bar")
        self.addToolBar(self.menubar)

        self.labelbar = LabelBar(self.menubar, "Label Bar")
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.labelbar)

        self.bg = QLabel()
        self.setCentralWidget(self.bg)
        self.bglayout = QHBoxLayout()
        self.bglayout.setContentsMargins(0, 0, 0, 0)
        self.bglayout.setSpacing(0)
        self.bg.setLayout(self.bglayout)

        self.filebar = FileBar(self.menubar)
        self.canvas = Canvas(self.menubar, self.labelbar, self.filebar)

        self.bglayout.addLayout(self.canvas, 85)
        self.bglayout.addLayout(self.filebar, 15)


    def initKeys(self):
        mv = 20
        z = 0.4

        self.zin_shortcut = QShortcut(QKeySequence('q'), self)
        self.zin_shortcut.activated.connect(lambda: self.canvas.zoomCanvas(z))

        self.zout_shortcut = QShortcut(QKeySequence('e'), self)
        self.zout_shortcut.activated.connect(lambda: self.canvas.zoomCanvas(-z))

        self.up_shortcut = QShortcut(QKeySequence('w'), self)
        self.up_shortcut.activated.connect(lambda: self.canvas.panCanvas(0, mv))

        self.left_shortcut = QShortcut(QKeySequence('a'), self)
        self.left_shortcut.activated.connect(lambda: self.canvas.panCanvas(mv, 0))

        self.down_shortcut = QShortcut(QKeySequence('s'), self)
        self.down_shortcut.activated.connect(lambda: self.canvas.panCanvas(0, -mv))

        self.right_shortcut = QShortcut(QKeySequence('d'), self)
        self.right_shortcut.activated.connect(lambda: self.canvas.panCanvas(-mv, 0))

        self.fill_shortcut = QShortcut(QKeySequence('f'), self)
        self.fill_shortcut.activated.connect(lambda: self.canvas.modeCanvas())

        self.next_label_shortcut = QShortcut(QKeySequence('right'), self)
        self.next_label_shortcut.activated.connect(lambda: self.labelbar.switchLabel(1))

        self.prev_label_shortcut = QShortcut(QKeySequence('left'), self)
        self.prev_label_shortcut.activated.connect(lambda: self.labelbar.switchLabel(-1))

class MenuBar(QToolBar):
    addLabelSignal = QtCore.pyqtSignal(list)

    def __init__(self, *args, **kwargs):
        super(QToolBar, self).__init__(*args, **kwargs)

        self.saveAction = QAction("Save Mask(s)", self)
        self.addAction(self.saveAction)

        self.importAction = QAction("Import Labels", self)
        self.importAction.triggered.connect(self.onImport)
        self.addAction(self.importAction)

        self.inferenceAction = QAction("Run Inference", self)
        self.inferenceAction.triggered.connect(self.onInference)
        self.addAction(self.inferenceAction)

    def onSave(self, s):
        print("save clicked")

    def onImport(self, s):
        path = QFileDialog.getOpenFileName(self, "Open Label text file", "Text files (*.txt)")

        if all(path):
            labels = open(str(path[0])).read().split('\n')[:MAX_CODES]
            self.addLabelSignal.emit(labels)

    def onInference(self, s):
        print("inference clicked")


class LabelBar(QToolBar):
    labelCanvasSignal = QtCore.pyqtSignal(int)

    def __init__(self, menubar, *args, **kwargs):
        super(QToolBar, self).__init__(*args, **kwargs)

        self.menubar = menubar
        self.menubar.addLabelSignal.connect(self.addLabels)

        # self.setMovable(False)

        self.labelActions = QActionGroup(self)
        self.labelActions.setExclusive(True)

    def addLabels(self, labels):
        self.clear()
        for lact in self.labelActions.actions():
            self.labelActions.removeAction(lact)

        for i, label in enumerate(labels, 0):
            box = QLabel()
            box.setStyleSheet("background-color:" + COLORS[i] + ";")
            box.setMaximumHeight(10)
            box.setMaximumWidth(5)
            self.addWidget(box)

            lact = QAction(label)
            lact.setCheckable(True)
            lact.toggled.connect(lambda state, _=i: self.labelCanvasSignal.emit(_))

            self.labelActions.addAction(lact)
            self.addAction(lact)

    def switchLabel(self, inc):
        try:
            pos = self.labelActions.actions().index(self.labelActions.checkedAction()) 
            pos = (pos+inc) % len(self.labelActions.actions())
            self.labelActions.actions()[pos].setChecked(True)
        except:
            pass


class FileBar(QVBoxLayout):
    addToCanvasSignal = QtCore.pyqtSignal(list, int)
    saveCanvasSignal = QtCore.pyqtSignal(object, bool)

    def __init__(self, menubar, *args, **kwargs):
        super(QVBoxLayout, self).__init__(*args, **kwargs)
        self.setSpacing(0)

        self.filelist = QListWidget()
        self.filelist.setViewMode(1)
        self.filelist.horizontalScrollBar().setEnabled(False)
        self.addWidget(self.filelist)

        self.buttonlayout = QHBoxLayout()
        self.addLayout(self.buttonlayout)
        self.buttonlayout.setSpacing(0)

        self.addPathsButton = QPushButton()
        self.addPathsButton.setIcon(QApplication.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        self.addPathsButton.clicked.connect(self.addPaths)
        self.buttonlayout.addWidget(self.addPathsButton)

        self.removePathButton = QPushButton()
        self.removePathButton.setIcon(QApplication.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.removePathButton.clicked.connect(self.removePath)
        self.buttonlayout.addWidget(self.removePathButton)

        self.savePathsButton = QPushButton()
        self.savePathsButton.setIcon(QApplication.style().standardIcon(QStyle.SP_DriveHDIcon))
        self.savePathsButton.clicked.connect(lambda: self.saveCanvasSignal.emit(self.filelist.currentItem(), False))
        self.buttonlayout.addWidget(self.savePathsButton)

    def addPaths(self):
        paths = QFileDialog.getOpenFileNames(self.filelist, "Open image file(s)", "Images (*.png *.jpg)")[0]
        mask_paths = []

        self.filelist.setIconSize(self.filelist.size() *0.9)
        for path in paths:
            item = QListWidgetItem(path.split("/")[-1], self.filelist)
            item.setToolTip(path)
            item.setIcon(QIcon(QPixmap(path)))

            if os.path.exists(toMaskPath(path)):
                mask_paths.append(toMaskPath(path))

        self.addToCanvasSignal.emit(paths, 0)
        self.addToCanvasSignal.emit(mask_paths, 1)
        
    def removePath(self):
        self.filelist.takeItem(self.filelist.currentRow())


class Canvas(QStackedLayout):
    def __init__(self, menubar, labelbar, filebar, *args, **kwargs):
        super(QStackedLayout, self).__init__(*args, **kwargs)
        self.labelbar = labelbar
        self.labelbar.labelCanvasSignal.connect(self.labelCanvas)

        self.filebar = filebar
        self.filebar.filelist.currentItemChanged.connect(self.cycleCanvas)
        self.filebar.addToCanvasSignal.connect(self.addToCanvas)
        self.filebar.saveCanvasSignal.connect(self.saveCanvas)

        self.setStackingMode(QStackedLayout.StackAll)
        self.shapemode = False

        self.imagelayer = Layer()
        self.masklayer = DrawLayer()
        self.hintlayer = DrawLayer()

        self.layers = [self.imagelayer, self.masklayer, self.hintlayer]
        for layer in self.layers:
            self.addWidget(layer)

        self.layers[-1].setMouseTracking(True)
        self.layers[-1].installEventFilter(self)

    def zoomCanvas(self, z):
        for layer in self.layers:
            layer.zoom += z
            layer.update()

    def panCanvas(self, x, y):
        for layer in self.layers:
            layer.pan.setX(layer.pan.x()+x)
            layer.pan.setY(layer.pan.y()+y)
            layer.update()
        
    def labelCanvas(self, n):
        for layer in self.layers:
            if hasattr(layer, 'current_label'):
                layer.current_label = n

    def addToCanvas(self, paths, n):
        for path in paths:
            if n is self.layers.index(self.masklayer):
                self.layers[n].storedpx.update({path : img2px(QImage(path))})
            else:
                self.layers[n].storedpx.update({path : QPixmap(path)})

    def saveCanvas(self, current, all=False):
        maskdir = os.path.dirname(list(self.masklayer.storedpx)[0])
        if not os.path.exists(maskdir):
            os.mkdir(maskdir)

        if current:
            self.masklayer.storedpx.update({toMaskPath(current.toolTip()) : self.masklayer.px})
            px = self.masklayer.storedpx.get(toMaskPath(current.toolTip()))
            px2img(px).save(toMaskPath(current.toolTip()), "PNG")
            current.setText(current.text().replace(" (unsaved)", ""))

       #    for path, px in self.masklayer.storedpx.items():
       #        if os.path.exists(path):
       #            existing_paths.append(path)
       #        else:
       #            px2img(px).save(path, "PNG")
       #            current.setText(path.replace(" (unsaved)"))

        # if existing_paths:
        #     msg = QMessageBox(QMessageBox.Warning, "Overwrite warning", "Existing paths were found for the file(s): "\
        #             +'\n'.join([os.path.basename(path) for path in existing_paths])\
        #             +"\n\nContinue with overwrite?")
        #     msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        #     msg.exec()
        #     if msg.result() == QMessageBox.Ok:
        #         for path in existing_paths:
        #             px2img(px).save(path, "PNG")
        #             current.setText(current.text().replace(" (unsaved)", ""))


    def cycleCanvas(self, current, previous):
        if previous:
            if self.masklayer.written:
                self.masklayer.storedpx.update({toMaskPath(previous.toolTip()) : self.masklayer.px})
                previous.setText(previous.text() + " (unsaved)")
                self.masklayer.written = False
            previous.setIcon(QIcon(quickOverlay([QPixmap(previous.toolTip()), self.masklayer.px], [1, 0.3])))

        if current:
            self.imagelayer.px = self.imagelayer.storedpx[current.toolTip()]
            size = self.imagelayer.px.size()

            try:
                self.masklayer.px = self.masklayer.storedpx[toMaskPath(current.toolTip())]
            except:
                self.masklayer.px = QPixmap(size)
                self.masklayer.px.fill(QtCore.Qt.transparent)

            self.hintlayer.px = QPixmap(size)
            self.hintlayer.px.fill(QtCore.Qt.transparent)

        for layer in self.layers:
            layer.reset()

    def modeCanvas(self):
        self.hintlayer.px.fill(QtCore.Qt.transparent)
        self.hintlayer.points.clear()
        self.hintlayer.update()
        self.shapemode = not self.shapemode

    def eventFilter(self, obj, event):
        if self.shapemode:
            if event.type() == QtCore.QEvent.MouseButtonPress:
                if (event.button() == QtCore.Qt.LeftButton):
                    self.hintlayer.drawPolygon(self.hintlayer.scale(event.pos()), fill=False)
                    self.masklayer.points.append(self.masklayer.scale(event.pos()))
                if (event.button() == QtCore.Qt.RightButton):
                    self.masklayer.points = self.hintlayer.points
                    self.masklayer.drawPolygon(pos=None, fill=True)
                    return True
        else:
            if event.type() == QtCore.QEvent.MouseButtonPress:
                if (event.button() == QtCore.Qt.LeftButton):
                    self.masklayer.drawCircle(self.masklayer.scale(event.pos()))
                    return True
            if (event.type() == QtCore.QEvent.MouseMove):
                if event.buttons() & QtCore.Qt.LeftButton:
                    self.masklayer.drawCircle(self.masklayer.scale(event.pos()))
                self.hintlayer.drawCircle(self.hintlayer.scale(event.pos()), shadow=False)
                return True
            if (event.type() == QtCore.QEvent.Wheel):
                self.masklayer.sizeTool(event.angleDelta().y())
                self.hintlayer.sizeTool(event.angleDelta().y())
                self.hintlayer.drawCircle(self.hintlayer.scale(event.pos()), shadow=False)
                return True

        return False


class Layer(QLabel):
    def __init__(self, *args, **kwargs):
        super(QLabel, self).__init__(*args, **kwargs)

        self.storedpx = {}
        self.px = QPixmap()

        self.factor = QtCore.QPointF()
        self.origin = QtCore.QPointF()

        self.reset()

    def reset(self):
        self.zoom = 1
        self.pan = QtCore.QPointF(0, 0)
        self.update()

    def scale(self, p):
        p.setX((p.x()-self.origin.x()-self.pan.x())*self.factor.x())
        p.setY((p.y()-self.origin.y()-self.pan.y())*self.factor.y())
        return p

    def paintEvent(self, event):
        if self.px.isNull():
            return

        qp = QPainter(self)
        try:
            qp.setOpacity(self.opacity)
        except:
            pass

        scaled_px = self.px.scaled(self.size()*self.zoom, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        self.factor.setX(self.px.width()/scaled_px.width())
        self.factor.setY(self.px.height()/scaled_px.height())
        self.origin = QtCore.QPointF((self.width()-scaled_px.width())/2, (self.height()-scaled_px.height())/2)

        qp.drawPixmap(self.origin.x()+self.pan.x(), self.origin.y()+self.pan.y(), scaled_px)

    def resizeEvent(self, event):
        self.reset()


class DrawLayer(Layer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.opacity=0.3
        self.written = False
        self.current_label = 0
        self.toolrad = 25
        self.points = []

    def sizeTool(self, delta):
        if delta > 0:
            self.toolrad += 3
        elif delta < 1:
            self.toolrad -= 3

    def drawCircle(self, pos, shadow=True):
        self.written = True

        if self.px.isNull():
            return
        if not shadow:
            self.px.fill(QtCore.Qt.transparent)

        qp = QPainter(self.px)
        qp.setCompositionMode(QPainter.CompositionMode_Source)
        qp.setPen(QtCore.Qt.NoPen)
        qp.setBrush(QBrush(QColor(COLORS[self.current_label]), QtCore.Qt.SolidPattern))

        qp.drawEllipse(pos, self.toolrad, self.toolrad)
        self.update()

    def drawPolygon(self, pos=None, fill=False):
        self.written = True

        qp = QPainter(self.px)
        qp.setCompositionMode(QPainter.CompositionMode_Source)

        if pos:
            self.points.append(pos)
        poly = QPolygonF(self.points)

        if fill:
            qp.setPen(QtCore.Qt.NoPen)
            qp.setBrush(QBrush(QColor(COLORS[self.current_label]), QtCore.Qt.SolidPattern))
            self.points.clear()
        else:
            self.px.fill(QtCore.Qt.transparent)
            qp.setPen(QPen(QColor(COLORS[self.current_label]), 5))

        qp.drawConvexPolygon(poly)
        self.update()


window = MainWindow()
window.show()

app.exec_()
