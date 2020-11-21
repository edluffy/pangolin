
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QAbstractItemView, QComboBox, QDialog, QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout


class ExportSettingsDialog(QDialog):
    def __init__(self, parent, fnames):
        super().__init__(parent)
        self.setWindowTitle("Export Settings")
        self.file_formats = ["PascalVOC (XML)", "COCO (JSON)", "YOLOv3 (XML)", "Image Mask (PNG)"]
        self.fnames = fnames

        self.file_list = QListWidget()
        self.file_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.file_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.file_list.setTextElideMode(Qt.ElideLeft)
        self.file_list.sortItems(Qt.AscendingOrder)
        self.file_list.addItems(self.fnames)
        self.file_list.selectAll()

        self.format_selector = QComboBox()
        self.format_selector.addItems(self.file_formats)

        self.cancel_button = QPushButton("Cancel")
        self.export_button = QPushButton("Export")
        self.cancel_button.clicked.connect(self.reject)
        self.export_button.clicked.connect(self.accept)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.main_layout.addWidget(QLabel("Select Files:"))
        self.main_layout.addWidget(self.file_list)
        self.main_layout.addWidget(QLabel("Export Format:"))
        self.main_layout.addWidget(self.format_selector)

        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.export_button)

    def selected_fnames(self):
        return [item.text() for item in self.file_list.selectedItems()]

    def file_format(self):
        return self.format_selector.currentText()
