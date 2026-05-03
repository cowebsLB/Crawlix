"""On-page audit — titles, meta, headings, lightweight scoring."""

from __future__ import annotations

from selectolax.parser import HTMLParser


def audit_html(html: str, url: str) -> tuple[float, list[dict], dict[str, float]]:
    tree = HTMLParser(html)
    issues: list[dict] = []
    title_el = tree.css_first("title")
    title = title_el.text().strip() if title_el and title_el.text() else ""
    if not title:
        issues.append(
            {
                "id": "missing_title",
                "severity": "high",
                "category": "metadata",
                "message": "Document has no <title>",
                "evidence": {"url": url},
            }
        )
    elif len(title) < 15:
        issues.append(
            {
                "id": "short_title",
                "severity": "low",
                "category": "metadata",
                "message": "Title is very short",
                "evidence": {"length": len(title)},
            }
        )

    desc = tree.css_first('meta[name="description"]')
    if not desc or not desc.attributes.get("content"):
        issues.append(
            {
                "id": "missing_meta_description",
                "severity": "medium",
                "category": "metadata",
                "message": "Missing meta description",
                "evidence": {},
            }
        )

    h1s = tree.css("h1")
    if len(h1s) == 0:
        issues.append(
            {
                "id": "missing_h1",
                "severity": "medium",
                "category": "content",
                "message": "No H1 heading",
                "evidence": {},
            }
        )
    elif len(h1s) > 1:
        issues.append(
            {
                "id": "multiple_h1",
                "severity": "low",
                "category": "content",
                "message": "Multiple H1 elements",
                "evidence": {"count": len(h1s)},
            }
        )

    score = max(0.0, 100.0 - 15 * len([i for i in issues if i["severity"] == "high"]))
    score -= 8 * len([i for i in issues if i["severity"] == "medium"])
    score -= 3 * len([i for i in issues if i["severity"] == "low"])
    cats = {"metadata": score, "content": score}
    return score, issues, cats
