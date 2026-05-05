from __future__ import annotations

from crawlix.ui import svg_icons


def test_svg_icon_module_exposes_raster_api() -> None:
    assert callable(svg_icons.svg_icon_colored)
