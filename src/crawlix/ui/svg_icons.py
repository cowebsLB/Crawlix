"""Monochrome navigation icons (vector raster). SVG sources live in ``crawlix/resources/icons/`` for design edits."""

from __future__ import annotations

from math import cos, pi, sin

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

_ICON_CACHE: dict[tuple[str, int, str], QIcon] = {}


def _pen(color: QColor, pixel: int) -> QPen:
    w = max(1.2, pixel / 14.0)
    return QPen(color, w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)


def _paint_icon(basename: str, pixel: int, color: QColor) -> QPixmap:
    pm = QPixmap(pixel, pixel)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(_pen(color, pixel))
    p.setBrush(Qt.BrushStyle.NoBrush)
    m = pixel * 0.12
    s = pixel - 2 * m

    def x(t: float) -> float:
        return m + t * s

    def y(t: float) -> float:
        return m + t * s

    if basename == "menu":
        for i in range(3):
            yy = y(0.22 + i * 0.28)
            p.drawLine(QPointF(x(0.08), yy), QPointF(x(0.92), yy))
    elif basename == "dashboard":
        p.drawLine(QPointF(x(0.5), y(0.12)), QPointF(x(0.12), y(0.42)))
        p.drawLine(QPointF(x(0.5), y(0.12)), QPointF(x(0.88), y(0.42)))
        p.drawLine(QPointF(x(0.12), y(0.42)), QPointF(x(0.12), y(0.88)))
        p.drawLine(QPointF(x(0.88), y(0.42)), QPointF(x(0.88), y(0.88)))
        p.drawLine(QPointF(x(0.12), y(0.88)), QPointF(x(0.88), y(0.88)))
        p.drawLine(QPointF(x(0.38), y(0.88)), QPointF(x(0.38), y(0.55)))
        p.drawLine(QPointF(x(0.62), y(0.55)), QPointF(x(0.62), y(0.88)))
    elif basename == "crawl":
        for cx, cy in ((0.22, 0.28), (0.78, 0.28), (0.5, 0.78)):
            p.drawEllipse(QPointF(x(cx), y(cy)), s * 0.07, s * 0.07)
        p.drawLine(QPointF(x(0.28), y(0.33)), QPointF(x(0.42), y(0.48)))
        p.drawLine(QPointF(x(0.72), y(0.33)), QPointF(x(0.58), y(0.48)))
        p.drawLine(QPointF(x(0.48), y(0.58)), QPointF(x(0.38), y(0.72)))
        p.drawLine(QPointF(x(0.52), y(0.58)), QPointF(x(0.62), y(0.72)))
    elif basename == "audit":
        p.drawRect(int(x(0.1)), int(y(0.12)), int(s * 0.38), int(s * 0.62))
        p.drawEllipse(QPointF(x(0.62), y(0.35)), s * 0.12, s * 0.12)
        p.drawLine(QPointF(x(0.72), y(0.45)), QPointF(x(0.88), y(0.62)))
        p.drawLine(QPointF(x(0.22), y(0.55)), QPointF(x(0.38), y(0.55)))
    elif basename == "keywords":
        p.drawEllipse(QPointF(x(0.42), y(0.42)), s * 0.18, s * 0.18)
        p.drawLine(QPointF(x(0.58), y(0.58)), QPointF(x(0.88), y(0.88)))
        p.drawLine(QPointF(x(0.28), y(0.38)), QPointF(x(0.52), y(0.38)))
        p.drawLine(QPointF(x(0.28), y(0.48)), QPointF(x(0.45), y(0.48)))
    elif basename == "citations":
        p.drawEllipse(QPointF(x(0.5), y(0.38)), s * 0.22, s * 0.28)
        p.drawLine(QPointF(x(0.5), y(0.66)), QPointF(x(0.5), y(0.88)))
        p.drawEllipse(QPointF(x(0.5), y(0.35)), s * 0.08, s * 0.08)
    elif basename == "local":
        p.drawLine(QPointF(x(0.1), y(0.88)), QPointF(x(0.9), y(0.88)))
        p.drawLine(QPointF(x(0.18), y(0.88)), QPointF(x(0.18), y(0.35)))
        p.drawLine(QPointF(x(0.82), y(0.88)), QPointF(x(0.82), y(0.35)))
        p.drawLine(QPointF(x(0.18), y(0.35)), QPointF(x(0.5), y(0.15)))
        p.drawLine(QPointF(x(0.82), y(0.35)), QPointF(x(0.5), y(0.15)))
        p.drawLine(QPointF(x(0.38), y(0.88)), QPointF(x(0.38), y(0.55)))
        p.drawLine(QPointF(x(0.62), y(0.55)), QPointF(x(0.62), y(0.88)))
    elif basename == "integrations":
        p.drawLine(QPointF(x(0.2), y(0.5)), QPointF(x(0.8), y(0.5)))
        p.drawEllipse(QPointF(x(0.2), y(0.5)), s * 0.08, s * 0.08)
        p.drawEllipse(QPointF(x(0.8), y(0.5)), s * 0.08, s * 0.08)
        p.drawLine(QPointF(x(0.2), y(0.35)), QPointF(x(0.35), y(0.35)))
        p.drawLine(QPointF(x(0.2), y(0.65)), QPointF(x(0.35), y(0.65)))
        p.drawLine(QPointF(x(0.8), y(0.35)), QPointF(x(0.65), y(0.35)))
        p.drawLine(QPointF(x(0.8), y(0.65)), QPointF(x(0.65), y(0.65)))
    elif basename == "reports":
        p.drawLine(QPointF(x(0.15), y(0.88)), QPointF(x(0.85), y(0.88)))
        p.drawLine(QPointF(x(0.15), y(0.88)), QPointF(x(0.15), y(0.22)))
        p.drawLine(QPointF(x(0.85), y(0.88)), QPointF(x(0.85), y(0.22)))
        p.drawLine(QPointF(x(0.15), y(0.22)), QPointF(x(0.85), y(0.22)))
        for bx in (0.28, 0.46, 0.64):
            p.drawLine(QPointF(x(bx), y(0.72)), QPointF(x(bx), y(0.38)))
    elif basename == "settings":
        cx, cy = x(0.5), y(0.5)
        r = s * 0.14
        p.drawEllipse(QPointF(cx, cy), r, r)
        for i in range(8):
            ang = (i / 8.0) * 2 * pi - pi / 2
            x0 = cx + cos(ang) * r * 0.55
            y0 = cy + sin(ang) * r * 0.55
            x1 = cx + cos(ang) * r * 1.15
            y1 = cy + sin(ang) * r * 1.15
            p.drawLine(QPointF(x0, y0), QPointF(x1, y1))
    else:
        p.drawEllipse(QPointF(x(0.5), y(0.5)), s * 0.2, s * 0.2)
    p.end()
    return pm


def svg_icon_colored(basename: str, pixel: int, color: QColor) -> QIcon:
    """Return a square ``QIcon`` for ``basename`` (slug), tinted with ``color``."""
    hexname = color.name(QColor.NameFormat.HexRgb)
    key = (basename, pixel, hexname)
    hit = _ICON_CACHE.get(key)
    if hit is not None:
        return hit
    pm = _paint_icon(basename, pixel, color)
    icon = QIcon(pm)
    _ICON_CACHE[key] = icon
    return icon
