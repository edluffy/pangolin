import pytest
from pytestqt.qt_compat import qt_api

import os

from src.converters.pascal_voc import pascal_voc_write, pascal_voc_read
from src.converters.image_mask import image_mask_write
from src.converters.yolo import yolo_write, yolo_read

from app import MainWindow

def test_image_mask(app_anno, qtbot):
    mask_folder = os.path.join(app_anno.file_widget.file_model.rootPath(), "Masks")

    im_paths = app_anno.interface.scene.change_stacks.keys()
    for p in im_paths:
        image_mask_write(app_anno.interface, p, mask_folder)
        pre, ext = os.path.splitext(os.path.basename(p))
        xp = os.path.join(mask_folder, pre+".png")
        assert os.path.isfile(xp) == True

        os.remove(xp)


def test_pascal_voc(app_anno, qtbot):
    # count = len(app_anno.interface.map)
    im_paths = app_anno.interface.scene.change_stacks.keys()

    ex_paths = []
    for p in im_paths:
        pascal_voc_write(app_anno.interface, p)
        pre, ext = os.path.splitext(p)
        xp = pre+".xml"
        assert os.path.isfile(xp) == True
        ex_paths.append(xp)

    app_anno.clear_project()
    qtbot.wait(1000)

    for xp in ex_paths:
        pascal_voc_read(app_anno.interface, xp)

        os.remove(xp)

    # TODO: Add this when project saves undo stack too
    # assert count == len(app_anno.interface.map)


def test_yolo(app_anno, qtbot):
    # count = len(app_anno.interface.map)
    im_paths = app_anno.interface.scene.change_stacks.keys()

    ex_paths = []
    for p in im_paths:
        yolo_write(app_anno.interface, p)
        pre, ext = os.path.splitext(p)
        xp = pre+".txt"
        assert os.path.isfile(xp) == True
        ex_paths.append(xp)

    app_anno.clear_project()
    qtbot.wait(1000)

    for xp in ex_paths:
        yolo_read(app_anno.interface, xp)

        os.remove(xp)

    # TODO: Add this when project saves undo stack too
    # assert count == len(app_anno.interface.map)
