import pytest

from PyQt5.QtCore import QItemSelectionModel

def test_basic_interface(app_anno, qtbot):
    assert len(app_anno.interface.map) > 0

    app_anno.interface.switch_label(3)

def test_selection(app_anno, qtbot):
    itf = app_anno.interface

    # for row in range(itf.model.rowCount()):
    #     idx = itf.model.indexFromItem(itf.model.item(row))
    #     qtbot.wait(1000)
    #     itf.tree.selectionModel().select(idx, QItemSelectionModel.Select)

    # qtbot.mousePress(app.graphics_view.viewport(), qt_api.QtCore.Qt.LeftButton, pos=p1)
