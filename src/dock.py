from PyQt5.QtCore import QDir, QEvent, QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QIcon, QPixmap
from PyQt5.QtWidgets import (QDockWidget, QFileDialog, QFileIconProvider,
                             QFileSystemModel, QItemDelegate, QListView, QStyle, QStyleOptionViewItem, QStyledItemDelegate, QTreeView, QVBoxLayout, QWidget)

from utils import pango_get_icon


class PangoDockWidget(QDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setWindowTitle(title)
        self.setContentsMargins(0, 0, 0, 0)

        self.bg = QWidget()
        self.bg_layout = QVBoxLayout(self.bg)
        self.setWidget(self.bg)

        self.setTitleBarWidget(QWidget())

class PangoLabelWidget(PangoDockWidget):
    def __init__(self, title, tree_view, parent=None):
        super().__init__(title, parent)
        self.setFixedWidth(250)
        self.tree_view = tree_view

        self.tree_view.setSelectionMode(QTreeView.ExtendedSelection)
        #self.tree_view.setStyleSheet(
        #    "QTreeView::indicator:checked:enabled{ image: url(:icons/eye_on.png)} \
        #     QTreeView::indicator:unchecked{ image: url(:icons/eye_off.png)}")

        self.setWidget(self.tree_view)

class PangoUndoWidget(PangoDockWidget):
    def __init__(self, title, undo_view, parent=None):
        super().__init__(title, parent)
        self.setFixedWidth(250)
        self.undo_view = undo_view

        self.undo_view.setCleanIcon(pango_get_icon("save"))
        self.undo_view.setEmptyLabel("Last save state")

        self.setWidget(self.undo_view)

    #class IconDelegate(QItemDelegate):
    #    def __init__(self, parent):
    #        super().__init__(parent)

    #    def paint(self, painter, option, idx):
    #        super().paint(painter, option, idx)

    #        text = idx.data()

    #        if text.startswith("Created "):
    #            shape_name = text.split("Created ", 1)[1].split()[0].lower()
    #            icon = pango_get_icon(shape_name)
    #        else:
    #            icon = pango_get_icon("save")

    #        rect = QRect(QPoint(), option.decorationSize)
    #        rect.moveCenter(option.rect.center())

    #        icon.paint(painter, rect, Qt.AlignVCenter)

    #    def sizeHint(self, option, idx):
    #        return QSize(16, 24)


class PangoFileWidget(PangoDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setFixedWidth(160)

        self.file_model = QFileSystemModel()
        self.file_model.setFilter(QDir.Files | QDir.NoDotAndDotDot)
        self.file_model.setNameFilters(["*.jpg", "*.png"])
        self.file_model.setNameFilterDisables(False)
        self.th_provider = ThumbnailProvider()
        self.file_model.setIconProvider(self.th_provider)

        self.file_view = QListView()
        self.file_view.setModel(self.file_model)
        self.file_view.setViewMode(QListView.IconMode)
        self.file_view.setFlow(QListView.LeftToRight)
        self.file_view.setIconSize(QSize(150, 150))
        
        self.setWidget(self.file_view)

class ThumbnailProvider(QFileIconProvider):
    def __init__(self):
        super().__init__()

    def icon(self, type: 'QFileIconProvider.IconType'):
        fn = type.filePath()

        if fn.endswith(".jpg") or fn.endswith(".png"):
            th = QPixmap(QSize(100, 100))
            th = th.scaledToHeight(125, Qt.FastTransformation)
            th.load(fn)
            return QIcon(th)
        else:
            return super().icon(type)
