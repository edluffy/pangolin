
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPainter, QPixmap


def image_mask_write(interface, fpath, folder):
    pre, ext = os.path.splitext(os.path.basename(fpath))
    fname = pre+".png"

    px = interface.scene.px
    ret_vis = interface.scene.reticle.isVisible()

    interface.scene.clearSelection()
    interface.scene.px = QPixmap(px.size())
    interface.scene.reticle.setVisible(False)
    for item in interface.scene.items():
        if hasattr(item, "force_opaque"):
            item.force_opaque = True
    interface.scene.invalidate(interface.scene.sceneRect())

    img = QImage(px.size(), QImage.Format_ARGB32)
    img.fill(Qt.transparent)

    painter = QPainter(img)
    interface.scene.render(painter)
    img.save(os.path.join(folder, fname))
    painter.end()

    # Return scene state
    interface.scene.px = px
    interface.scene.reticle.setVisible(ret_vis)
    for item in interface.scene.items():
        if hasattr(item, "force_opaque"):
            item.force_opaque = False
    interface.scene.invalidate(interface.scene.sceneRect())
