"""Keyword phrase templates from site type, country, brand, topic, and location hints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from crawlix.db.models import Location, Project

SITE_TYPE_CHOICES: list[tuple[str, str]] = [
    ("local_service", "Local / service business"),
    ("ecommerce", "E-commerce / retail"),
    ("saas", "SaaS / software product"),
    ("blog_content", "Blog / content / media"),
    ("portfolio", "Portfolio / creative agency"),
    ("corporate", "Corporate / institutional"),
    ("marketplace", "Marketplace / classifieds"),
    ("other", "Other / general"),
]

# ISO 3166-1 alpha-2 subset (extend as needed)
COUNTRY_NAMES: dict[str, str] = {
    "US": "United States",
    "GB": "United Kingdom",
    "CA": "Canada",
    "AU": "Australia",
    "DE": "Germany",
    "FR": "France",
    "LB": "Lebanon",
    "AE": "United Arab Emirates",
    "SA": "Saudi Arabia",
    "EG": "Egypt",
    "IN": "India",
    "JP": "Japan",
    "BR": "Brazil",
    "MX": "Mexico",
    "ES": "Spain",
    "IT": "Italy",
    "NL": "Netherlands",
    "BE": "Belgium",
    "CH": "Switzerland",
    "SE": "Sweden",
    "NO": "Norway",
    "PL": "Poland",
    "PT": "Portugal",
    "IE": "Ireland",
    "NZ": "New Zealand",
    "SG": "Singapore",
    "ZA": "South Africa",
}

COUNTRY_CHOICES: list[tuple[str, str]] = [("", "(use first location if set)")] + sorted(
    ((c, f"{c} — {n}") for c, n in COUNTRY_NAMES.items()), key=lambda x: x[1]
)


@dataclass(frozen=True)
class TemplateContext:
    site_type: str
    country_code: str
    brand: str
    topic: str
    city: str
    region: str
    domain: str
    year: str


def _domain_label(default_domain: str | None) -> str:
    if not default_domain:
        return ""
    raw = default_domain.strip()
    if "://" in raw:
        return urlparse(raw).netloc.split(":")[0] or raw
    return raw.split("/")[0]


def merge_context_from_project(session: Session, project: Project) -> dict[str, Any]:
    """
    Merge ``project.seo_context_json`` with sensible defaults from the first
    project location and project name/domain.
    """
    base: dict[str, Any] = dict(project.seo_context_json or {})
    loc = session.scalar(select(Location).where(Location.project_id == project.id).order_by(Location.id.asc()).limit(1))
    if not base.get("primary_country_code") and loc and loc.country_code:
        base["primary_country_code"] = str(loc.country_code).upper()[:2]
    if not base.get("brand_name"):
        if loc and loc.business_name:
            base["brand_name"] = loc.business_name.strip()
        else:
            base["brand_name"] = (project.name or "").strip()
    if not base.get("primary_topic"):
        base["primary_topic"] = ""
    if not base.get("site_type"):
        base["site_type"] = "other"
    if not base.get("language"):
        base["language"] = "en"
    base.setdefault("primary_country_code", "")
    return base


def _fill(template: str, tokens: dict[str, str]) -> str:
    out = template
    for k, v in tokens.items():
        out = out.replace("{" + k + "}", v)
    return " ".join(out.split()).strip()


def _tokens(ctx: TemplateContext) -> dict[str, str]:
    cc = (ctx.country_code or "").upper()[:2]
    cname = COUNTRY_NAMES.get(cc, cc or "")
    return {
        "brand": ctx.brand or "your brand",
        "topic": ctx.topic or "your service",
        "city": ctx.city or "",
        "region": ctx.region or "",
        "country": cc,
        "country_name": cname,
        "domain": ctx.domain or "",
        "year": ctx.year,
    }


def _pack_local(tokens: dict[str, str]) -> list[str]:
    city = tokens["city"]
    out = [
        "{brand} near me",
        "{brand} reviews",
        "best {topic}",
        "hire {topic}",
        "{brand} {city}",
        "{topic} {city}",
        "{topic} near me",
        "{brand} {country_name}",
        "{topic} {country_name}",
        "{brand} phone number",
        "{brand} opening hours",
    ]
    if city:
        out += ["{topic} in {city}", "cheap {topic} {city}"]
    if city and tokens["region"]:
        out.append("{brand} {city} {region}")
    return [x for x in (_fill(p, tokens) for p in out) if x]


def _pack_ecommerce(tokens: dict[str, str]) -> list[str]:
    return [
        _fill(p, tokens)
        for p in (
            "buy {topic} online",
            "{topic} price",
            "{topic} sale",
            "{brand} {topic}",
            "{topic} shipping {country_name}",
            "{topic} discount",
            "{brand} shop",
            "{topic} reviews",
            "best {topic} {country_name}",
        )
    ]


def _pack_saas(tokens: dict[str, str]) -> list[str]:
    return [
        _fill(p, tokens)
        for p in (
            "{topic} software",
            "best {topic} tool",
            "{topic} pricing",
            "{brand} login",
            "{brand} vs competitors",
            "{topic} for teams",
            "{topic} API",
            "{topic} integration",
            "{brand} demo",
            "{topic} free trial",
        )
    ]


def _pack_blog(tokens: dict[str, str]) -> list[str]:
    return [
        _fill(p, tokens)
        for p in (
            "how to {topic}",
            "{topic} guide",
            "{topic} tips {year}",
            "what is {topic}",
            "{topic} examples",
            "{topic} tutorial",
            "{brand} blog",
            "{topic} best practices",
        )
    ]


def _pack_portfolio(tokens: dict[str, str]) -> list[str]:
    phrases = (
        "{brand} portfolio",
        "{topic} designer",
        "{topic} agency {city}",
        "hire {brand}",
        "{topic} case studies",
        "{brand} work examples",
    )
    return [x for p in phrases if (x := _fill(p, tokens))]


def _pack_corporate(tokens: dict[str, str]) -> list[str]:
    return [
        _fill(p, tokens)
        for p in (
            "{brand} contact",
            "{brand} careers",
            "{brand} about",
            "{topic} solutions",
            "{brand} investor relations",
            "{brand} press",
        )
    ]


def _pack_marketplace(tokens: dict[str, str]) -> list[str]:
    return [
        _fill(p, tokens)
        for p in (
            "{topic} marketplace",
            "sell {topic} online",
            "{brand} sellers",
            "buy used {topic}",
            "{topic} listing",
        )
    ]


def _pack_other(tokens: dict[str, str]) -> list[str]:
    return [
        _fill(p, tokens)
        for p in (
            "{brand}",
            "{topic}",
            "{brand} {topic}",
            "{topic} {country_name}",
            "{domain}",
        )
        if _fill(p, tokens)
    ]


def suggest_phrases(
    ctx: TemplateContext,
    *,
    existing_lower: set[str] | None = None,
    max_suggestions: int = 48,
) -> list[str]:
    """Return deduplicated phrase suggestions; skip those already in ``existing_lower`` (casefold)."""
    tokens = _tokens(ctx)
    existing_lower = existing_lower or set()
    packs: dict[str, list[str]] = {
        "local_service": _pack_local(tokens),
        "ecommerce": _pack_ecommerce(tokens),
        "saas": _pack_saas(tokens),
        "blog_content": _pack_blog(tokens),
        "portfolio": _pack_portfolio(tokens),
        "corporate": _pack_corporate(tokens),
        "marketplace": _pack_marketplace(tokens),
        "other": _pack_other(tokens),
    }
    raw = packs.get(ctx.site_type) or packs["other"]
    seen: set[str] = set()
    out: list[str] = []
    for phrase in raw:
        p = phrase.strip()
        if len(p) < 2 or len(p) > 500:
            continue
        k = p.casefold()
        if k in seen or k in existing_lower:
            continue
        seen.add(k)
        out.append(p)
        if len(out) >= max_suggestions:
            break
    return out


def context_from_merged(merged: dict[str, Any], project: Project, session: Session) -> TemplateContext:
    loc = session.scalar(select(Location).where(Location.project_id == project.id).order_by(Location.id.asc()).limit(1))
    city = (loc.city or "").strip() if loc else ""
    region = (loc.region or "").strip() if loc else ""
    cc = str(merged.get("primary_country_code") or "").upper()[:2]
    if not cc and loc and loc.country_code:
        cc = str(loc.country_code).upper()[:2]
    year = str(datetime.now(UTC).year)
    return TemplateContext(
        site_type=str(merged.get("site_type") or "other"),
        country_code=cc,
        brand=str(merged.get("brand_name") or project.name or "").strip(),
        topic=str(merged.get("primary_topic") or "").strip(),
        city=city,
        region=region,
        domain=_domain_label(project.default_domain),
        year=year,
    )
