"""Citation template placeholders — must match docs/citation-placeholders.md."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import quote

KNOWN = frozenset(
    {
        "phone_digits",
        "phone_e164",
        "business_slug",
        "business_query",
        "city",
        "region",
        "postal_code",
        "country_code",
    }
)


@dataclass
class LocationFields:
    business_name: str
    city: str | None
    region: str | None
    postal_code: str | None
    country_code: str | None
    primary_phone_e164: str | None


def _slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "business"


def _digits_e164(phone: str | None) -> str:
    if not phone:
        return ""
    return re.sub(r"\D", "", phone)


def expand_template(template: str, loc: LocationFields) -> str:
    unknown = set(re.findall(r"\{(\w+)\}", template)) - KNOWN
    if unknown:
        raise ValueError(f"Unknown placeholders: {unknown}")

    phone_digits = _digits_e164(loc.primary_phone_e164)
    phone_e164 = loc.primary_phone_e164 or ""
    business_slug = _slug(loc.business_name)
    business_query = quote(loc.business_name, safe="")
    city = quote(loc.city or "", safe="")
    region = quote(loc.region or "", safe="")
    postal_code = loc.postal_code or ""
    country_code = (loc.country_code or "").upper()

    return template.format(
        phone_digits=phone_digits,
        phone_e164=phone_e164,
        business_slug=business_slug,
        business_query=business_query,
        city=city,
        region=region,
        postal_code=postal_code,
        country_code=country_code,
    )
