# Keyword targeting and template suggestions

Crawlix can suggest **starter keyword phrases** from a small **project targeting** profile: **site type**, **primary country**, **brand**, **topic**, and the **first saved location** (city / region / country) when useful. Suggestions are **English phrase packs** today; they dedupe and skip phrases already on the project.

---

## Where it lives in the app

1. Open a project and go to **Keywords**.
2. **Project targeting (templates)** — set **site type**, **primary country** (optional; defaults from the first **Location** if the country field is set there), **brand name**, **primary topic**, then **Save targeting**.
3. **Template keyword ideas** — **Generate suggestions**, tick the phrases you want, **Add checked to project**.

Added keywords get `tags_json` including `source: "template"` and the saved `site_type` so exports or future UI can filter them.

---

## Database

| Column | Table | Notes |
|--------|--------|--------|
| `seo_context_json` | `projects` | Nullable JSON object; see keys below. |

**Migration:** Alembic revision `e5a1c2d3b4f0` (`add_project_seo_context_json`). If the column is missing, the UI shows a short message to run migrations (`alembic upgrade head` or your usual flow — see [setup.md](setup.md)).

### JSON keys (current)

| Key | Type | Meaning |
|-----|------|---------|
| `site_type` | string | One of the internal IDs in **Site types** below. Default `other`. |
| `primary_country_code` | string | ISO 3166-1 alpha-2 (e.g. `LB`, `US`). Default from first `locations.country_code` if unset in JSON. |
| `brand_name` | string | Display / marketing name. Default: first location `business_name`, else project `name`. |
| `primary_topic` | string | Short vertical or product line (e.g. “plumbing”, “CRM”). May be empty. |
| `language` | string | Reserved for future localized packs; default `en`. |

Extra keys are preserved if you merge JSON manually later.

---

## Site types and phrase packs

Internal `site_type` values map to packs in `src/crawlix/services/keywords/templates.py`:

| `site_type` | UI label (approx.) |
|-------------|---------------------|
| `local_service` | Local / service business |
| `ecommerce` | E-commerce / retail |
| `saas` | SaaS / software product |
| `blog_content` | Blog / content / media |
| `portfolio` | Portfolio / creative agency |
| `corporate` | Corporate / institutional |
| `marketplace` | Marketplace / classifieds |
| `other` | Other / general |

Packs use placeholders `{brand}`, `{topic}`, `{city}`, `{region}`, `{country_name}`, `{domain}`, `{year}`. Empty segments are dropped so you do not get double spaces; some phrases are omitted when **city** is missing (e.g. portfolio “agency {city}”).

---

## Countries

`COUNTRY_NAMES` in `templates.py` is a **curated subset** of ISO alpha-2 codes with English display names (US, GB, CA, AU, DE, FR, LB, AE, …). Extend the dict and `COUNTRY_CHOICES` when you need more regions.

---

## Code entry points

| Piece | Path |
|-------|------|
| Merge saved JSON + defaults | `merge_context_from_project(session, project)` |
| Build `TemplateContext` | `context_from_merged(merged, project, session)` |
| Suggestions | `suggest_phrases(ctx, existing_lower=..., max_suggestions=48)` |

Unit tests: `tests/unit/test_keyword_templates.py`.

---

## Known limitations

- **Wizard:** New project flow does not yet set `seo_context_json`; targeting is edited on the Keywords tab after creation.
- **Locales:** Packs are English-oriented; `language` is stored but not yet used to switch packs.
- **Keyword table** does not yet show a “from template” column (data is in `tags_json`).

See [known-limitations.md](known-limitations.md) for broader product scope.
