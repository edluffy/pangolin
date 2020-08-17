
class PangoFileWidget(PangoDockWidget):
    def __init__(self, model, title, parent=None):
        super().__init__(title, parent)

        # Model and Views
        self.model = model
        self.view = QListView()
        self.view.setViewMode(QListView.IconMode)
        self.view.setIconSize(QtCore.QSize(150, 150))
        self.view.setModel(self.model)

        # Toolbars and menus
        self.view.doubleClicked.connect

        # Widgets
        self.import_button = QPushButton("Select Images")
        self.import_button.pressed.connect(self.import_)

        # Layouts
        self.layout = QVBoxLayout(self.bg)
        self.layout.addWidget(self.import_button)
        self.layout.addWidget(self.view)

    def import_(self):
        paths, _ = QFileDialog.getOpenFileNames(self,
            "Open image file(s)", "Images (*.png *.jpg)")
        self.model.files.extend(paths)
        self.model.layoutChanged.emit()

class FileModel(QtCore.QAbstractListModel):
    def __init__(self, files, parent=None):
        super().__init__(parent)

        self.files = files or []

    def data(self, index, role):
        if role == Qt.DisplayRole:
            fn = os.path.basename(self.files[index.row()]) 
            return fn
        if role == Qt.DecorationRole:
            icon = QIcon(self.files[index.row()])
            return icon
        if role == Qt.ToolTipRole:
            return self.files[index.row()]

    def rowCount(self, index):
        return len(self.files)
