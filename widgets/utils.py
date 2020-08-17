from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAction, QActionGroup, QDockWidget, QToolBar,
                             QWidget)


class PangoDockWidget(QDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)

        self.setWindowTitle(title)
        self.setFloating(True)

        self.bg = QWidget()
        self.setWidget(self.bg)

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
