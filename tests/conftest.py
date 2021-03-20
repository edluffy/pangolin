import pytest

from app import MainWindow

@pytest.fixture
def app(qtbot):
    app = MainWindow()
    qtbot.addWidget(app)
    app.show()
    app.load_images(fpath="tests/resources")

    # Clearing autoloaded project, must wait until
    # images are loaded in
    qtbot.wait(1000)
    app.clear_project()

    return app

# App with annotations preloaded in
@pytest.fixture # P
def app_anno(qtbot):
    app = MainWindow()
    qtbot.addWidget(app)
    app.show()
    app.load_images(fpath="tests/resources")
    return app

