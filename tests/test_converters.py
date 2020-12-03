import pytest
from pytestqt.qt_compat import qt_api

from app import MainWindow

@pytest.fixture
def app(qtbot):
    app = MainWindow()
    qtbot.addWidget(app)
    app.show()
    app.load_images(fpath="tests/resources")
    return app

def test_pascal_voc(app, qtbot):
    pass
    

