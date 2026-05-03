# Citation URL template placeholders

Resolver code in `crawlix.services.citations.placeholders` must match this dictionary. **YAML packs** are validated at load time against these keys.

| Placeholder | Expansion | Example |
|-------------|-----------|---------|
| `{phone_digits}` | E.164 digits only (no `+`, spaces, punctuation) | `13105551212` |
| `{phone_e164}` | Full E.164 with `+` | `+13105551212` |
| `{business_slug}` | Lowercase slug from `business_name` (alnum + hyphen) | `joes-pizza` |
| `{business_query}` | URL-encoded `business_name` | `Joe%27s%20Pizza` |
| `{city}` | URL-encoded city | `Los%20Angeles` |
| `{region}` | URL-encoded `locations.region` | `CA` |
| `{postal_code}` | As stored | `90001` |
| `{country_code}` | ISO 3166-1 alpha-2 upper | `US` |

## Logging rule

Do not log fully expanded URLs containing PII unless the user explicitly enables a second-confirm debug mode.

## Nominatim / OSM

Use **strict rate limits** (see [Usage Policy](https://operations.osmfoundation.org/policies/nominatim/)). Crawlix starter YAML includes Nominatim as an **optional** helper row — prefer self-hosted or heavy throttling for production workloads.
