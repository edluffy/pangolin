from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDockWidget, QWidget

class PangoDockWidget(QDockWidget):
    def __init__(self, title):
        super(PangoDockWidget, self).__init__(title)

        self.setFloating(True)
        self.setWindowTitle(title)

        self.bg = QWidget()
        self.setWidget(self.bg)

class PangoLabelWidget(PangoDockWidget):
    def __init__(self, *args, **kwargs):
        super(PangoLabelWidget, self).__init__(*args, **kwargs)

        # Test Data
        test_poly = QPolygonF([QPointF(10, 10), QPointF(
            20, 10), QPointF(20, 20), QPointF(10, 20)])

        root_node = Node("this is the root")

        label0   = LabelNode("breadboard", root_node, PALETTE[0])
        label0_0 = PolygonNode(test_poly, label0)
        label0_1 = PolygonNode(None, label0)

        label1   = LabelNode("wire",  root_node, PALETTE[1])
        label1_0 = PolygonNode(None, label1)

        label2   = LabelNode("push button", root_node, PALETTE[2])
        label2_0 = PolygonNode(None, label2)
        label2_1 = PolygonNode(None, label2)
        label2_2 = PolygonNode(None, label2)

        # Model and Views
        self.model = NodeModel(root_node)

        self.view = QTreeView()
        self.view.setModel(self.model)
        for i in range(0, 2):
            self.view.resizeColumnToContents(i)


        # Toolbars and menus

        # Widgets
        self.line_edit = QLineEdit()
        self.line_edit.returnPressed.connect(self.add)
        self.line_edit.setPlaceholderText("Enter a new label")

        self.delete_button = QPushButton("-")
        self.delete_button.pressed.connect(self.delete)
        self.add_button = QPushButton("+")
        self.add_button.pressed.connect(self.add)

        # Layouts
        self.layout = QVBoxLayout(self.bg)
        self.button_layout = QHBoxLayout()

        self.layout.addWidget(self.line_edit)
        self.layout.addWidget(self.view)
        self.layout.addLayout(self.button_layout)

        self.button_layout.addWidget(self.delete_button)
        self.button_layout.addWidget(self.add_button)
    
    def add(self):
        text = self.line_edit.text()
        if not text == '':
            color = QtGui.QColor(PALETTE[(len(self.model.data)+1)%len(PALETTE)])
            self.model.data.append((text, color))
            self.model.layoutChanged.emit()
        self.line_edit.clear()
    def delete(self):
        idxs = self.view.selectedIndexes()
        if idxs:
            if idxs[0].row() < len(self.model.data):
                del self.model.data[idxs[0].row()]
                self.model.layoutChanged.emit()
            else:
                self.view.clearSelection()

class PangoFileWidget(PangoDockWidget):
    def __init__(self, *args, **kwargs):
        super(PangoFileWidget, self).__init__(*args, **kwargs)

        # Data
        test_files = ['/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/001.jpg',
                      '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/002.jpg',
                      '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/003.jpg',
                      '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/004.jpg',
                      '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/005.jpg',
                      '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/006.jpg',
                      '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/007.jpg',
                      '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/008.jpg',
                      '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/009.jpg',
                      '/Users/edluffy/Downloads/drive-download-20200728T084549Z-001/010.jpg']

        # Model and Views
        self.model = FileModel(test_files)
        self.view = QListView()
        self.view.setViewMode(QListView.IconMode)
        self.view.setIconSize(QtCore.QSize(150, 150))
        self.view.setModel(self.model)

        # Toolbars and menus

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
