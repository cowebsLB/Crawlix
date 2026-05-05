# UI Design Tokens

## Implementation

Runtime palette lives in **`src/crawlix/ui/design_tokens.py`**. Stylesheets **`src/crawlix/ui/styles/app_dark.qss`** and **`app_light.qss`** use `%%token_name%%` placeholders; :func:`crawlix.ui.styles.load_stylesheet` interpolates them. Spacing helpers (`spacing_px`, `radius_px`) are for Python layouts (e.g. shell chrome).

For the full UI redesign backlog, see **[full-ui-redesign-backlog.md](full-ui-redesign-backlog.md)**.

## Personality
Crawlix feels calm by default, sharp when something matters.

## Color Semantics
- Action Accent (electric cyan/blue): primary CTA, active nav, active row, focused actions.
- Insight Tone (amber): non-critical insight grouping and secondary emphasis.
- Danger (red): critical/failure/destructive states only.
- Success (muted green): completed/healthy states.
- Neutral surfaces: dark graphite/navy in dark mode; warm slate/off-white in light mode.

## Typography
- Titles: strong weight, larger scale.
- Sections: medium-high emphasis.
- Body/meta: compact, legible, scan-friendly.

## Density
- Default is comfortable-compact.
- Tables keep consistent row heights with truncation + tooltip patterns.

## Motion
- Row selection feedback transition.
- Inspector slide/fade-in.
- Job progress state animation.
- Reduced-motion mode must preserve clarity without movement.
