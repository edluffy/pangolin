from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QAction, QSizePolicy, QApplication, QActionGroup, QDockWidget, QToolBar,
                             QWidget, QMenuBar,QMenu)

PangoPalette = [QColor('#e6194b'), QColor('#3cb44b'), QColor('#ffe119'),
                QColor('#4363d8'), QColor('#f58231'), QColor('#911eb4'),
                QColor('#46f0f0'), QColor('#f032e6'), QColor('#bcf60c'),
                QColor('#fabebe'), QColor('#008080'), QColor('#e6beff'),
                QColor('#9a6324'), QColor('#fffac8'), QColor('#800000'),
                QColor('#aaffc3'), QColor('#808000'), QColor('#ffd8b1'),
                QColor('#000075'), QColor('#808080')]

class PangoDockWidget(QDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)

        self.setWindowTitle(title)
        self.setFloating(True)

        self.bg = QWidget()
        self.setWidget(self.bg)

        #self.setTitleBarWidget(QWidget())


class PangoToolBarWidget(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.pan_action = QAction("Pan")
        self.brush_action = QAction("Brush")
        self.rect_action = QAction("Rect")
        self.poly_action = QAction("Poly")

        self.action_group = QActionGroup(self)
        self.action_group.setExclusive(True)

        self.action_group.addAction(self.pan_action)
        self.action_group.addAction(self.brush_action)
        self.action_group.addAction(self.rect_action)
        self.action_group.addAction(self.poly_action)

        actions = self.action_group.actions()
        self.addActions(actions)
        for action in actions:
            action.setCheckable(True)


class PangoMenuBarWidget(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        self.prefs_action = QAction(QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_MessageBoxInformation), "Preferences")

        self.open_images_action = QAction(QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_FileDialogNewFolder), "Open Images")

        self.import_labels_action = QAction(QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_FileDialogNewFolder), "Import Labels")

        self.save_action = QAction(QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_DialogSaveButton), "Save Masks")

        self.run_action = QAction(QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_DialogOkButton), "Run Inference")

        self.filebar_action = QAction(QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_TitleBarMaxButton), "FileBar")

        self.labelbar_action = QAction(QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_TitleBarMaxButton), "LabelBar")

        spacer_left = QWidget()
        spacer_right = QWidget()
        spacer_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.addAction(self.prefs_action)
        self.addWidget(spacer_left)
        self.addAction(self.open_images_action)
        self.addAction(self.import_labels_action)
        self.addAction(self.save_action)
        self.addAction(self.run_action)
        self.addWidget(spacer_right)
        self.addAction(self.filebar_action)
        self.addAction(self.labelbar_action)
