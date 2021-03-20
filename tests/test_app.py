import pytest

def test_basic(app, qtbot):
    assert app.isVisible() == True
    assert app.windowTitle() == "Pangolin"
    assert app.file_widget.file_model.rootPath() == "tests/resources"

