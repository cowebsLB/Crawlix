# Dashboard Action Model

## Goal
Dashboard answers: "What should I do next?"

## Primary Modules
1. Next best actions
2. Needs attention now
3. Recent outcomes

## Action Rules
- Every dashboard module must provide actionable navigation.
- Passive stats are secondary and only included when they influence decisions.

## Deep-Link Targets
- jobs
- crawl
- audit
- future: keywords/citations action links

## See also
Richer **`NextActionItem`** fields and cockpit routing: [next-refactors-and-risks.md](../next-refactors-and-risks.md) §5.

## Deep-link behavior (current)
**Run selected action** uses **`decode_dashboard_list_item`** ([`dashboard_action_runner.py`](../../src/crawlix/ui/dashboard_action_runner.py)) then **`resolve_dashboard_action`** ([`controllers_actions.py`](../../src/crawlix/ui/controllers_actions.py)).

- **`audit:page:{id}`** — opens **Audit**, selects that **page** row; if missing from the latest **200** audits, **`query_audit_results_rows(..., prioritize_page_id=…)`** pins that page’s newest audit first.
- **`crawl:start`** — **`DashboardActionRoute.focus_crawl_seeds`**, focuses the **seed URLs** field; optional **`suggested_filter`** on the list item (JSON in **`UserRole+3`**). Default fallback action uses **`{"apply_saved_crawl_view": true}`** so the stored **Crawl** saved view is applied before focus (same shapes as [`SavedView`](../../src/crawlix/ui/saved_views.py) partial keys: **`search`**, **`http_filter`**, **`depth_filter`**, **`max_inbound`**, **`min_outbound`**, **`dup_only`**).
