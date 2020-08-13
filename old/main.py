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

global to_mask_path
global img2px
global px2img
global quick_overlay


def to_mask_path(path):
    fn = "M_"+os.path.basename(os.path.splitext(path)[0]+".png")
    return os.path.join(os.path.dirname(path), "Masks", fn)


def img2px(img):
    layers = []
    px = QPixmap().fromImage(img)
    for i, color in enumerate(COLORS, 0):
        tmp = QPixmap(px.size())
        tmp.fill(QColor(int(color[1:], 16)))
        tmp.setMask(px.createMaskFromColor(QColor.fromRgb(i, i, i),
                                           QtCore.Qt.MaskOutColor))
        layers.append(tmp)
    return quick_overlay(layers, [1 for _ in layers])


def px2img(px):
    layers = []
    for i, color in enumerate(COLORS, 0):
        tmp = QPixmap(px.size())
        tmp.fill(QColor.fromRgb(i, i, i))
        tmp.setMask(px.createMaskFromColor(QColor(int(color[1:], 16)),
                                           QtCore.Qt.MaskOutColor))
        layers.append(tmp)
    px = quick_overlay(layers, [1 for _ in layers])
    return px.toImage().convertToFormat(QImage.Format_Grayscale8)


def quick_overlay(layers, opacities=[]):
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
        self.init_keys()

        self.menu_bar = MenuBar("Menu Bar")
        self.addToolBar(self.menu_bar)

        self.label_bar = LabelBar(self.menu_bar, "Label Bar")
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.label_bar)

        self.bg = QLabel()
        self.setCentralWidget(self.bg)
        self.bglayout = QHBoxLayout()
        self.bglayout.setContentsMargins(0, 0, 0, 0)
        self.bglayout.setSpacing(0)
        self.bg.setLayout(self.bglayout)

        self.file_bar = FileBar(self.menu_bar)
        self.canvas = Canvas(self.menu_bar, self.label_bar, self.file_bar)

        self.bglayout.addLayout(self.canvas, 85)
        self.bglayout.addLayout(self.file_bar, 15)

    def init_keys(self):
        mv = 20
        z = 0.4

        self.zin_shortcut = QShortcut(QKeySequence('q'), self)
        self.zin_shortcut.activated.connect(lambda: self.canvas.zoom_canvas(z))

        self.zout_shortcut = QShortcut(QKeySequence('e'), self)
        self.zout_shortcut.activated.connect(
            lambda: self.canvas.zoom_canvas(-z))

        self.up_shortcut = QShortcut(QKeySequence('w'), self)
        self.up_shortcut.activated.connect(
            lambda: self.canvas.pan_canvas(0, mv))

        self.left_shortcut = QShortcut(QKeySequence('a'), self)
        self.left_shortcut.activated.connect(
            lambda: self.canvas.pan_canvas(mv, 0))

        self.down_shortcut = QShortcut(QKeySequence('s'), self)
        self.down_shortcut.activated.connect(
            lambda: self.canvas.pan_canvas(0, -mv))

        self.right_shortcut = QShortcut(QKeySequence('d'), self)
        self.right_shortcut.activated.connect(
            lambda: self.canvas.pan_canvas(-mv, 0))

        self.fill_shortcut = QShortcut(QKeySequence('f'), self)
        self.fill_shortcut.activated.connect(lambda: self.canvas.mode_canvas())

        self.next_label_shortcut = QShortcut(QKeySequence('right'), self)
        self.next_label_shortcut.activated.connect(
            lambda: self.label_bar.switch_label(1))

        self.prev_label_shortcut = QShortcut(QKeySequence('left'), self)
        self.prev_label_shortcut.activated.connect(
            lambda: self.label_bar.switch_label(-1))


class MenuBar(QToolBar):
    addLabelSignal = QtCore.pyqtSignal(list)

    def __init__(self, *args, **kwargs):
        super(QToolBar, self).__init__(*args, **kwargs)

        self.importAction = QAction("Import Labels", self)
        self.importAction.triggered.connect(self.on_import)
        self.addAction(self.importAction)

        self.inferenceAction = QAction("Run Inference", self)
        self.inferenceAction.triggered.connect(self.on_inference)
        self.addAction(self.inferenceAction)

    def on_import(self, s):
        path = QFileDialog.getOpenFileName(
            self, "Open Label text file", "Text files (*.txt)")

        if all(path):
            labels = open(str(path[0])).read().split('\n')[:MAX_CODES]
            self.addLabelSignal.emit(labels)

    def on_inference(self, s):
        print("inference clicked")


class LabelBar(QToolBar):
    labelCanvasSignal = QtCore.pyqtSignal(int)

    def __init__(self, menu_bar, *args, **kwargs):
        super(QToolBar, self).__init__(*args, **kwargs)

        self.menu_bar = menu_bar
        self.menu_bar.addLabelSignal.connect(self.add_labels)

        # self.setMovable(False)

        self.label_actions = QActionGroup(self)
        self.label_actions.setExclusive(True)

    def add_labels(self, labels):
        self.clear()
        for action in self.label_actions.actions():
            self.label_actions.removeAction(action)

        for i, label in enumerate(labels, 0):
            box = QLabel()
            box.setStyleSheet("background-color:" + COLORS[i] + ";")
            box.setMaximumHeight(10)
            box.setMaximumWidth(5)
            self.addWidget(box)

            action = QAction(label)
            action.setCheckable(True)
            action.toggled.connect(
                lambda state, _=i: self.labelCanvasSignal.emit(_))

            self.label_actions.addAction(action)
            self.addAction(action)

    def switch_label(self, inc):
        try:
            pos = self.label_actions.actions().index(self.label_actions.checkedAction())
            pos = (pos+inc) % len(self.label_actions.actions())
            self.label_actions.actions()[pos].setChecked(True)
        except:
            pass


class FileBar(QVBoxLayout):
    addToCanvasSignal = QtCore.pyqtSignal(list, int)
    saveCanvasSignal = QtCore.pyqtSignal(object, bool)

    def __init__(self, menu_bar, *args, **kwargs):
        super(QVBoxLayout, self).__init__(*args, **kwargs)
        self.setSpacing(0)

        self.file_list = QListWidget()
        self.file_list.setViewMode(1)
        self.file_list.horizontalScrollBar().setEnabled(False)
        self.addWidget(self.file_list)

        self.buttonlayout = QHBoxLayout()
        self.addLayout(self.buttonlayout)
        self.buttonlayout.setSpacing(0)

        self.addPathsButton = QPushButton()
        self.addPathsButton.setIcon(
            QApplication.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        self.addPathsButton.clicked.connect(self.add_paths)
        self.buttonlayout.addWidget(self.addPathsButton)

        self.removePathButton = QPushButton()
        self.removePathButton.setIcon(
            QApplication.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.removePathButton.clicked.connect(self.remove_path)
        self.buttonlayout.addWidget(self.removePathButton)

        self.savePathsButton = QPushButton()
        self.savePathsButton.setIcon(
            QApplication.style().standardIcon(QStyle.SP_DriveHDIcon))
        self.savePathsButton.clicked.connect(
            lambda: self.saveCanvasSignal.emit(self.file_list.currentItem(), False))
        self.buttonlayout.addWidget(self.savePathsButton)

    def add_paths(self):
        paths = QFileDialog.getOpenFileNames(
            self.file_list, "Open image file(s)", "Images (*.png *.jpg)")[0]
        mask_paths = []

        self.file_list.setIconSize(self.file_list.size() * 0.9)
        for path in paths:
            item = QListWidgetItem(path.split("/")[-1], self.file_list)
            item.setToolTip(path)
            item.setIcon(QIcon(QPixmap(path)))

            if os.path.exists(to_mask_path(path)):
                mask_paths.append(to_mask_path(path))

        self.addToCanvasSignal.emit(paths, 0)
        self.addToCanvasSignal.emit(mask_paths, 1)

    def remove_path(self):
        self.file_list.takeItem(self.file_list.currentRow())


class Canvas(QStackedLayout):
    def __init__(self, menu_bar, label_bar, file_bar, *args, **kwargs):
        super(QStackedLayout, self).__init__(*args, **kwargs)
        self.label_bar = label_bar
        self.label_bar.labelCanvasSignal.connect(self.label_canvas)

        self.file_bar = file_bar
        self.file_bar.file_list.currentItemChanged.connect(self.cycle_canvas)
        self.file_bar.addToCanvasSignal.connect(self.add_to_canvas)
        self.file_bar.saveCanvasSignal.connect(self.save_canvas)

        self.setStackingMode(QStackedLayout.StackAll)
        self.shape_mode = False

        self.image_layer = Layer()
        self.mask_layer = DrawLayer()
        self.hint_layer = DrawLayer()

        self.layers = [self.image_layer, self.mask_layer, self.hint_layer]
        for layer in self.layers:
            self.addWidget(layer)

        self.layers[-1].setMouseTracking(True)
        self.layers[-1].installEventFilter(self)

    def zoom_canvas(self, z):
        for layer in self.layers:
            layer.zoom += z
            layer.update()

    def pan_canvas(self, x, y):
        for layer in self.layers:
            layer.pan.setX(layer.pan.x()+x)
            layer.pan.setY(layer.pan.y()+y)
            layer.update()

    def label_canvas(self, n):
        for layer in self.layers:
            if hasattr(layer, 'current_label'):
                layer.current_label = n

    def add_to_canvas(self, paths, n):
        for path in paths:
            if n is self.layers.index(self.mask_layer):
                self.layers[n].stored_px.update({path: img2px(QImage(path))})
            else:
                self.layers[n].stored_px.update({path: QPixmap(path)})

    def save_canvas(self, current, all=False):
        mask_folder = os.path.dirname(list(self.mask_layer.stored_px)[0])
        if not os.path.exists(mask_folder):
            os.mkdir(mask_folder)

        if current:
            self.mask_layer.stored_px.update(
                {to_mask_path(current.toolTip()): self.mask_layer.px})
            px = self.mask_layer.stored_px.get(to_mask_path(current.toolTip()))
            px2img(px).save(to_mask_path(current.toolTip()), "PNG")
            current.setText(current.text().replace(" (unsaved)", ""))

       #    for path, px in self.mask_layer.stored_px.items():
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

    def cycle_canvas(self, current, previous):
        if previous:
            if self.mask_layer.written:
                self.mask_layer.stored_px.update(
                    {to_mask_path(previous.toolTip()): self.mask_layer.px})
                previous.setText(previous.text() + " (unsaved)")
                self.mask_layer.written = False
            previous.setIcon(QIcon(quick_overlay(
                [QPixmap(previous.toolTip()), self.mask_layer.px], [1, 0.3])))

        if current:
            self.image_layer.px = self.image_layer.stored_px[current.toolTip()]
            size = self.image_layer.px.size()

            try:
                self.mask_layer.px = self.mask_layer.stored_px[to_mask_path(
                    current.toolTip())]
            except:
                self.mask_layer.px = QPixmap(size)
                self.mask_layer.px.fill(QtCore.Qt.transparent)

            self.hint_layer.px = QPixmap(size)
            self.hint_layer.px.fill(QtCore.Qt.transparent)

        for layer in self.layers:
            layer.reset()

    def mode_canvas(self):
        self.hint_layer.px.fill(QtCore.Qt.transparent)
        self.hint_layer.points.clear()
        self.hint_layer.update()
        self.shape_mode = not self.shape_mode

    def eventFilter(self, obj, event):
        if self.shape_mode:
            if event.type() == QtCore.QEvent.MouseButtonPress:
                if (event.button() == QtCore.Qt.LeftButton):
                    self.hint_layer.draw_polygon(
                        self.hint_layer.scale(event.pos()), fill=False)
                    self.mask_layer.points.append(
                        self.mask_layer.scale(event.pos()))
                if (event.button() == QtCore.Qt.RightButton):
                    self.mask_layer.points = self.hint_layer.points
                    self.mask_layer.draw_polygon(pos=None, fill=True)
                    return True
        else:
            if event.type() == QtCore.QEvent.MouseButtonPress:
                if (event.button() == QtCore.Qt.LeftButton):
                    self.mask_layer.draw_circle(
                        self.mask_layer.scale(event.pos()))
                    return True
            if (event.type() == QtCore.QEvent.MouseMove):
                if event.buttons() & QtCore.Qt.LeftButton:
                    self.mask_layer.draw_circle(
                        self.mask_layer.scale(event.pos()))
                self.hint_layer.draw_circle(
                    self.hint_layer.scale(event.pos()), shadow=False)
                return True
            if (event.type() == QtCore.QEvent.Wheel):
                self.mask_layer.size_tool(event.angleDelta().y())
                self.hint_layer.size_tool(event.angleDelta().y())
                self.hint_layer.draw_circle(
                    self.hint_layer.scale(event.pos()), shadow=False)
                return True

        return False


class Layer(QLabel):
    def __init__(self, *args, **kwargs):
        super(QLabel, self).__init__(*args, **kwargs)

        self.stored_px = {}
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

        scaled_px = self.px.scaled(
            self.size()*self.zoom, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        self.factor.setX(self.px.width()/scaled_px.width())
        self.factor.setY(self.px.height()/scaled_px.height())
        self.origin = QtCore.QPointF(
            (self.width()-scaled_px.width())/2, (self.height()-scaled_px.height())/2)

        qp.drawPixmap(self.origin.x()+self.pan.x(),
                      self.origin.y()+self.pan.y(), scaled_px)

    def resizeEvent(self, event):
        self.reset()


class DrawLayer(Layer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.opacity = 0.3
        self.written = False
        self.current_label = 0
        self.tool_rad = 25
        self.points = []

    def size_tool(self, delta):
        if delta > 0:
            self.toolrad += 3
        elif delta < 1:
            self.toolrad -= 3

    def draw_circle(self, pos, shadow=True):
        self.written = True

        if self.px.isNull():
            return
        if not shadow:
            self.px.fill(QtCore.Qt.transparent)

        qp = QPainter(self.px)
        qp.setCompositionMode(QPainter.CompositionMode_Source)
        qp.setPen(QtCore.Qt.NoPen)
        qp.setBrush(
            QBrush(QColor(COLORS[self.current_label]), QtCore.Qt.SolidPattern))

        qp.drawEllipse(pos, self.tool_rad, self.tool_rad)
        self.update()

    def draw_polygon(self, pos=None, fill=False):
        self.written = True

        qp = QPainter(self.px)
        qp.setCompositionMode(QPainter.CompositionMode_Source)

        if pos:
            self.points.append(pos)
        poly = QPolygonF(self.points)

        if fill:
            qp.setPen(QtCore.Qt.NoPen)
            qp.setBrush(
                QBrush(QColor(COLORS[self.current_label]), QtCore.Qt.SolidPattern))
            self.points.clear()
        else:
            self.px.fill(QtCore.Qt.transparent)
            qp.setPen(QPen(QColor(COLORS[self.current_label]), 5))

        qp.drawConvexPolygon(poly)
        self.update()


window = MainWindow()
window.show()

app.exec_()
