"""Semantic design tokens for Crawlix (dark/light).

QSS files under ``styles/`` use ``%%token_name%%`` placeholders; :func:`substitute_qss_tokens`
fills them from the active palette. Charts and icons can import the same RGB hex strings from
``colors_for_theme``.
"""

from __future__ import annotations

from typing import Final, Literal

ThemeMode = Literal["dark", "light"]

_SPACING_PX: Final[dict[str, int]] = {
    "2": 2,
    "4": 4,
    "8": 8,
    "12": 12,
    "16": 16,
    "24": 24,
    "32": 32,
}

_RADIUS_PX: Final[dict[str, int]] = {
    "sm": 4,
    "md": 6,
    "lg": 10,
    "pill": 999,
}


def spacing_px(scale: Literal["2", "4", "8", "12", "16", "24", "32"]) -> int:
    """Layout spacing scale (pixels). Used from Python layouts; mirrored in QSS."""
    return _SPACING_PX[scale]


def radius_px(kind: Literal["sm", "md", "lg", "pill"]) -> int:
    """Corner radius in pixels for programmatic styling."""
    return _RADIUS_PX[kind]


def colors_for_theme(mode: ThemeMode) -> dict[str, str]:
    """Semantic color names → hex. Shared by Matplotlib / SVG helpers later."""
    return dict(_PALETTES[mode])


def qss_substitutions(mode: ThemeMode) -> dict[str, str]:
    """Flat map for %%token%% substitution in stylesheet templates."""
    c = colors_for_theme(mode)
    px = _SPACING_PX
    rx = _RADIUS_PX
    return {
        **c,
        **{f"space_{k}": f"{v}px" for k, v in px.items()},
        **{f"radius_{k}": f"{v}px" for k, v in rx.items()},
    }


def substitute_qss_tokens(raw_qss: str, mode: ThemeMode) -> str:
    out = raw_qss
    for key, val in qss_substitutions(mode).items():
        out = out.replace(f"%%{key}%%", val)
    return out


# Dark / light palettes: names follow docs/ui/full-ui-redesign-backlog.md (surface.* → surface_*).

_PALETTES: Final[dict[ThemeMode, dict[str, str]]] = {
    "dark": {
        # Text
        "text_primary": "#e8e8e8",
        "text_secondary": "#cccccc",
        "text_muted": "#aaaaaa",
        "text_disabled": "#a0a0a0",
        "text_inverse": "#ffffff",
        "text_input": "#ffffff",
        "text_on_accent": "#ffffff",
        # Surfaces
        "surface_base": "#141a22",
        "surface_sunken": "#0f141c",
        "surface_raised": "#1a2230",
        "surface_overlay": "#1a2230",
        "surface_disabled": "#3c3c3c",
        "surface_scroll": "#1a2230",
        # Borders
        "border_subtle": "#3c3c3c",
        "border_default": "#444444",
        "border_strong": "#6a6a6a",
        "border_muted": "#555555",
        # Accent / selection
        "accent_action": "#00a8d6",
        "accent_hover": "#13b5e5",
        "accent_pressed": "#0b7fa2",
        "accent_focus": "#13b5e5",
        "accent_selection": "#264f78",
        # Status (reserved for semantic widgets / future pills)
        "status_success": "#3d8f6e",
        "status_warning": "#c9a227",
        "status_danger": "#c74242",
        "status_info": "#4a90c8",
        # Insight tone
        "accent_insight": "#d4a24c",
        # Priority cues
        "priority_now": "#c74242",
        "priority_soon": "#c9a227",
        "priority_later": "#6d7a88",
        # Scrollbar
        "scrollbar_thumb": "#5a5a5a",
        # Chrome
        "statusbar_bg": "#00a8d6",
        "statusbar_fg": "#ffffff",
    },
    "light": {
        "text_primary": "#202734",
        "text_secondary": "#333333",
        "text_muted": "#666666",
        "text_disabled": "#666666",
        "text_inverse": "#fdfcf9",
        "text_on_accent": "#fdfcf9",
        "text_input": "#0a0a0a",
        "surface_base": "#f6f4ef",
        "surface_sunken": "#fdfcf9",
        "surface_raised": "#ece8df",
        "surface_overlay": "#fdfcf9",
        "surface_disabled": "#eeeeee",
        "surface_scroll": "#ece8df",
        "border_subtle": "#cccccc",
        "border_default": "#cccccc",
        "border_strong": "#888888",
        "border_muted": "#cccccc",
        "accent_action": "#007fc7",
        "accent_hover": "#1190da",
        "accent_pressed": "#005a9e",
        "accent_focus": "#005a9e",
        "accent_selection": "#264f78",
        "status_success": "#2f6f4f",
        "status_warning": "#9a7400",
        "status_danger": "#b32d2d",
        "status_info": "#2a6f9f",
        "accent_insight": "#8a6300",
        "priority_now": "#b32d2d",
        "priority_soon": "#9a7400",
        "priority_later": "#666666",
        "scrollbar_thumb": "#b0b0b0",
        "statusbar_bg": "#007fc7",
        "statusbar_fg": "#fdfcf9",
    },
}
