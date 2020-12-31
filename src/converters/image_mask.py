import os
from item import PangoLabelGraphic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPixmap


def image_mask_write(interface, fpath, folder):
    pre, ext = os.path.splitext(os.path.basename(fpath))
    fname = pre+".png"

    px = interface.scene.px
    ret_vis = interface.scene.reticle.isVisible()

    interface.scene.clearSelection()
    interface.scene.px = QPixmap(px.size())
    interface.scene.px.fill(Qt.transparent)
    interface.scene.reticle.setVisible(False)
    for gfx in interface.scene.items():
        if hasattr(gfx, "force_opaque"):
            gfx.force_opaque = True

    saved_colors = {}
    for row in range(0, interface.model.rowCount()):
        label = interface.model.item(row)
        saved_colors[row] = label.color
        label.color = QColor(row+1, row+1, row+1)
        label.force_update()

    interface.scene.invalidate(interface.scene.sceneRect())

    img = QImage(px.size(), QImage.Format_ARGB32)
    img.fill(QColor(0, 0, 0))

    painter = QPainter(img)
    interface.scene.render(painter)

    img.save(os.path.join(folder, fname))
    painter.end()

    # Return scene state
    for row in range(0, interface.model.rowCount()):
        label = interface.model.item(row)
        label.color = saved_colors[row]
        label.force_update()

    interface.scene.px = px
    interface.scene.reticle.setVisible(ret_vis)
    for item in interface.scene.items():
        if hasattr(item, "force_opaque"):
            item.force_opaque = False
    interface.scene.invalidate(interface.scene.sceneRect())
