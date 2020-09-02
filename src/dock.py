from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import (QDockWidget, QFileDialog, QFileIconProvider, 
                             QFileSystemModel,  QListView,  QWidget)


class PangoDockWidget(QDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setWindowTitle(title)
        self.setContentsMargins(0, 0, 0, 0)

        self.bg = QWidget()
        self.setWidget(self.bg)

        self.setTitleBarWidget(QWidget())

class PangoLabelWidget(PangoDockWidget):
    def __init__(self, title, view, parent=None):
        super().__init__(title, parent)
        self.view = view
        self.setFixedWidth(200)

        # Widgets
        self.setWidget(self.view)


class PangoFileWidget(PangoDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setFixedWidth(160)

        self.file_model = QFileSystemModel()
        self.thumbnail_provider = ThumbnailProvider()
        self.file_model.setIconProvider(self.thumbnail_provider)

        self.file_view = QListView()
        self.file_view.setModel(self.file_model)
        self.file_view.setViewMode(QListView.IconMode)
        self.file_view.setFlow(QListView.LeftToRight)
        self.file_view.setIconSize(QSize(150, 150))

        # Widgets
        self.setWidget(self.file_view)

    def open(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        dialog.exec()

        self.file_model.setRootPath(dialog.directory().absolutePath())
        self.file_view.setRootIndex(self.file_model.index(self.file_model.rootPath()))


class ThumbnailProvider(QFileIconProvider):
    def __init__(self):
        super().__init__()
        pass

    def icon(self, type: 'QFileIconProvider.IconType'):
        fn = type.filePath()

        if fn.endswith(".jpg"):
            a = QPixmap(QSize(100, 100))
            a = a.scaledToHeight(125, Qt.FastTransformation)
            a.load(fn)
            return QIcon(a)
        else:
            return super().icon(type)
