from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QColor
#from PyQt5.QtWidgets import

from enum import Enum

from PyQt5.QtWidgets import QGraphicsItem

from resources import icons_rc

pango_palette = [QColor('#e6194b'), QColor('#3cb44b'), QColor('#ffe119'),
                 QColor('#4363d8'), QColor('#f58231'), QColor('#911eb4'),
                 QColor('#46f0f0'), QColor('#f032e6'), QColor('#bcf60c'),
                 QColor('#fabebe'), QColor('#008080'), QColor('#e6beff'),
                 QColor('#9a6324'), QColor('#fffac8'), QColor('#800000'),
                 QColor('#aaffc3'), QColor('#808000'), QColor('#ffd8b1'),
                 QColor('#000075'), QColor('#808080')]

pango_app_icon_color = QColor("grey")

def pango_get_palette(n):
    return pango_palette[n % len(pango_palette)]

def pango_get_icon(name, color=None):
    fn = ":/icons/"+name.lower().replace(" ", "_")+".png"
    px = QPixmap(fn)
    mask = px.createMaskFromColor(QColor('white'), Qt.MaskOutColor)
    px.fill(pango_app_icon_color if color is None else color)
    px.setMask(mask)
    return QIcon(px)

class PangoShapeType(Enum):
    Default = QGraphicsItem.UserType +1
    Path = QGraphicsItem.UserType + 2
    Rect = QGraphicsItem.UserType + 3
    Poly = QGraphicsItem.UserType + 4
    Dot = QGraphicsItem.UserType + 5


def pango_item_role_debug(role):
    return role_list[role]
role_list =  [
    "DisplayRole", "DecorationRole", "EditRole",
    "ToolTipRole", "StatusTipRole", "WhatsThisRole",
    "FontRole", "TextAlignmentRole", "BackgroundColorRole",
    "BackgroundRole", "TextColorRole", "ForegroundRole",
    "CheckStateRole", "AccessibleTextRole", "AccessibleDescriptionRole",
    "SizeHintRole", "InitialSortOrderRole", "DisplayPropertyRole",
    "DecorationPropertyRole", "ToolTipPropertyRole", "StatusTipPropertyRole",
    "WhatsThisPropertyRole", "UserRole"]

def pango_gfx_change_debug(change):
    return change_list[change]
change_list = [
    "ItemPositionChange", "ItemMatrixChange", "ItemVisibleChange",
    "ItemEnabledChange", "ItemSelectedChange", "ItemParentChange",
    "ItemChildAddedChange", "ItemChildRemovedChange", "ItemTransformChange",
    "ItemPositionHasChanged", "ItemTransformHasChanged", "ItemSceneChange",
    "ItemVisibleHasChanged", "ItemEnabledHasChanged", "ItemSelectedHasChanged",
    "ItemParentHasChanged", "ItemSceneHasChanged", "ItemCursorChange",
    "ItemCursorHasChanged", "ItemToolTipChange", "ItemToolTipHasChanged",
    "ItemFlagsChange", "ItemFlagsHaveChanged", "ItemZValueChange",
    "ItemZValueHasChanged", "ItemOpacityChange", "ItemOpacityHasChanged",
    "ItemScenePositionHasChanged", "ItemRotationChange", "ItemRotationHasChanged",
    "ItemScaleChange", "ItemScaleHasChanged", "ItemTransformOriginPointChange",
    "ItemTrasformOriginPointHasChanged" ]
