import pytest
from pytestqt.qt_compat import qt_api

from src.dock import PangoDockWidget

from PyQt5.QtWidgets import QFileSystemModel, QListView

def test_basic_dock(app):
    assert app.label_widget.isVisible() == True
    assert app.label_widget.windowTitle() == "Labels"

    assert app.undo_widget.isVisible() == True
    assert app.undo_widget.windowTitle() == "History"

    assert app.file_widget.isVisible() == True
    assert app.file_widget.windowTitle() == "Files"

def test_label_dock(app):
    assert app.label_widget.widget() == app.label_widget.tree_view

def test_undo_dock(app):
    assert app.undo_widget.widget() == app.undo_widget.undo_view

    # TODO: Add this when project saves undo stack too
    # app.undo_widget.redo()
    # assert app.undo_widget.undo_view.currentIndex().row() == 1
    # app.undo_widget.undo()
    # assert app.undo_widget.undo_view.currentIndex().row() == 0

def test_file_dock(app):
    assert app.file_widget.widget() == app.file_widget.file_view
    assert app.file_widget.file_model.iconProvider() == app.file_widget.th_provider

    assert app.file_widget.file_view.currentIndex().row() == 0
    app.file_widget.select_prev_image()
    assert app.file_widget.file_view.currentIndex().row() == 0
    app.file_widget.select_next_image()
    assert app.file_widget.file_view.currentIndex().row() == 1
    app.file_widget.select_prev_image()
    assert app.file_widget.file_view.currentIndex().row() == 0

