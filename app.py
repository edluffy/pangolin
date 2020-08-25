from bidict import bidict

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QStandardItemModel, QPixmap
from PyQt5.QtWidgets import (QApplication, QLabel, QLineEdit,
                             QListView, QMainWindow, QMenu, QPushButton,
                             QStatusBar, QVBoxLayout, QGraphicsItemGroup, QGraphicsPathItem, QTreeView, QGraphicsItem)

from widgets.canvas import PangoGraphicsScene, PangoGraphicsView
from widgets.file import PangoFileWidget
from widgets.label import PangoLabelWidget
from widgets.utils import PangoMenuBarWidget, PangoToolBarWidget

from item import PangoStandardItem

app = QApplication([])

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Pangolin")
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setGeometry(50, 50, 1000, 675)

        self.pango_item_map = bidict()

        # Toolbars and menus
        self.menu_bar = PangoMenuBarWidget()
        self.tool_bar = PangoToolBarWidget()
        self.addToolBar(Qt.LeftToolBarArea, self.tool_bar)


        # Widgets
        self.file_widget = PangoFileWidget("Files")

        self.file_widget.view.activated.connect(self.image_changed)
        self.tool_bar.action_group.triggered.connect(self.tool_changed)


        # Layouts
        #self.addToolBar(Qt.TopToolBarArea, self.menu_bar)
        self.addDockWidget(Qt.LeftDockWidgetArea,  self.file_widget)
        #self.setCentralWidget(self.canvas_widget)

    def image_changed(self, idx):
        # Model-View Land
        self.std_model = QStandardItemModel()
        self.std_view = QTreeView()
        self.std_view.setModel(self.std_model)

        self.std_model.dataChanged.connect(self.data_changed)
        self.std_model.rowsInserted.connect(self.std_inserted)
        self.std_view.selectionModel().selectionChanged.connect(self.selection_changed)

        # Graphics-View Land
        self.gfx_model = PangoGraphicsScene(self.pango_item_map)
        self.gfx_view = PangoGraphicsView(self.gfx_model)
        self.gfx_view.setInteractive(True)

        self.gfx_model.dataChanged.connect(self.data_changed)
        self.gfx_model.rowsInserted.connect(self.gfx_inserted)
        #self.gfx_model.selectionChanged.connect(self.selection_changed)

        # File-specific data
        title = idx.data(Qt.DisplayRole)
        path = idx.data(Qt.ToolTipRole)

        self.std_model.setHeaderData(0, Qt.Horizontal, title)
        self.gfx_model.addPixmap(QPixmap(path))

        # Widget extras
        self.label_widget = PangoLabelWidget(
            "Labels", self.pango_item_map, self.std_model, self.std_view)
        self.addDockWidget(Qt.LeftDockWidgetArea,  self.label_widget)

        self.setCentralWidget(self.gfx_view)


    def tool_changed(self, action):
        self.gfx_model.tool = action.text()

    def std_inserted(self, parent_idx, first, last):
        idx = self.std_model.index(first, 0, parent_idx)
        std_item = self.std_model.itemFromIndex(idx)

        gfx_item = QGraphicsItemGroup()
        gfx_item.setFlag(QGraphicsItem.ItemIsSelectable)

        self.gfx_model.addItem(gfx_item)
        self.pango_item_map[std_item.map_index()] = gfx_item

    def gfx_inserted(self, gfx_item, parent_gfx):
        parent_std = self.pango_item_map.inverse[parent_gfx]
        type = gfx_item.type()

        if type == 2:
            std_item = PangoStandardItem("Path", parent_std)
        else:
            return

        self.pango_item_map[std_item.map_index()] = gfx_item



    def selection_changed(self, selected, deselected):
        if selected.indexes() != []:
            s_idx = selected.indexes()[0]
            std_item = self.std_model.itemFromIndex(s_idx)

            gfx_item = self.pango_item_map[std_item.map_index()]
            gfx_item.setSelected(True)

        if deselected.indexes() != []:
            ds_idx = deselected.indexes()[0]
            std_item = self.std_model.itemFromIndex(ds_idx)

            gfx_item = self.pango_item_map[std_item.map_index()]
            gfx_item.setSelected(False)

            #parent_idx = s_idx.parent()
            #while parent_idx.isValid():
            #    s_idx = parent_idx
            #    parent_idx = s_idx.parent()
            #self.selected_std_item = self.model.itemFromIndex(s_idx)
            #self.selected_gfx_item = self.item_map[self.selected_std_item.map_index()]

    def data_changed(self, top_left, bottom_right, role):
        pass

window = MainWindow()
window.show()

app.exec_()
