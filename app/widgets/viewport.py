from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont
from PySide6.QtWidgets import QWidget


class CharacterPreview(QWidget):
    """Temporary visual placeholder; will be replaced by a real 3D viewport."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 420)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        gradient = QLinearGradient(0, 0, 0, rect.height())
        gradient.setColorAt(0, QColor("#202a3a"))
        gradient.setColorAt(1, QColor("#111720"))
        painter.fillRect(rect, QBrush(gradient))

        painter.setPen(QPen(QColor("#35465e"), 1))
        for x in range(0, rect.width(), 40):
            painter.drawLine(x, 0, x, rect.height())
        for y in range(0, rect.height(), 40):
            painter.drawLine(0, y, rect.width(), y)

        cx = rect.width() / 2
        cy = rect.height() / 2 + 35
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#a9c5e8"))
        painter.drawEllipse(QRectF(cx - 34, cy - 190, 68, 75))
        painter.setBrush(QColor("#547aa8"))
        painter.drawRoundedRect(QRectF(cx - 57, cy - 112, 114, 145), 24, 24)
        painter.setBrush(QColor("#3f6089"))
        painter.drawRoundedRect(QRectF(cx - 100, cy - 105, 42, 125), 18, 18)
        painter.drawRoundedRect(QRectF(cx + 58, cy - 105, 42, 125), 18, 18)
        painter.setBrush(QColor("#263f60"))
        painter.drawRoundedRect(QRectF(cx - 52, cy + 28, 43, 145), 16, 16)
        painter.drawRoundedRect(QRectF(cx + 9, cy + 28, 43, 145), 16, 16)

        painter.setPen(QColor("#dbe8f8"))
        font = QFont()
        font.setPointSize(11)
        painter.setFont(font)
        painter.drawText(18, 28, "角色预览区 · 示意模型")
        painter.setPen(QColor("#91a5bf"))
        painter.drawText(18, rect.height() - 18, "下一阶段：接入真实3D视口、模型旋转与GLB加载")
        painter.end()
