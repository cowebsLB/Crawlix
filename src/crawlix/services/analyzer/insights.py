from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

IssueSeverity = Literal["info", "low", "medium", "high", "critical"]
IssuePriority = Literal["later", "soon", "now"]
IssueConfidence = Literal["low", "medium", "high"]


class IssueCategory(StrEnum):
    TECHNICAL_HEALTH = "technical_health"
    INDEXABILITY = "indexability"
    DUPLICATION = "duplication"
    INTERNAL_LINKING = "internal_linking"
    METADATA = "metadata"
    PERFORMANCE = "performance"
    CONTENT_QUALITY = "content_quality"
    CRAWL_EFFICIENCY = "crawl_efficiency"


@dataclass(frozen=True)
class EvidenceItem:
    key: str
    value: str


@dataclass(frozen=True)
class InspectorInsight:
    category: str
    severity: IssueSeverity
    priority: IssuePriority
    confidence: IssueConfidence
    summary: str
    why_it_matters: str
    evidence: list[EvidenceItem]
    recommendation: str
    action_label: str | None = None
    action_target: str | None = None


_ID_CATEGORY_MAP: dict[str, IssueCategory] = {
    "missing_title": IssueCategory.METADATA,
    "short_title": IssueCategory.METADATA,
    "long_title": IssueCategory.METADATA,
    "missing_meta_description": IssueCategory.METADATA,
    "missing_h1": IssueCategory.CONTENT_QUALITY,
    "multiple_h1": IssueCategory.CONTENT_QUALITY,
    "missing_canonical": IssueCategory.DUPLICATION,
    "multiple_canonical_tags": IssueCategory.DUPLICATION,
    "duplicate_canonical_tags": IssueCategory.DUPLICATION,
    "canonical_mismatch": IssueCategory.DUPLICATION,
    "meta_noindex": IssueCategory.INDEXABILITY,
    "header_noindex": IssueCategory.INDEXABILITY,
    "robots_txt_blocked": IssueCategory.INDEXABILITY,
    "non_200_status": IssueCategory.TECHNICAL_HEALTH,
    "orphan_internal": IssueCategory.INTERNAL_LINKING,
    "no_internal_outlinks": IssueCategory.INTERNAL_LINKING,
    "deep_url_path": IssueCategory.CRAWL_EFFICIENCY,
    "duplicate_title_site": IssueCategory.DUPLICATION,
    "multiple_paths_same_destination": IssueCategory.DUPLICATION,
    "duplicate_title_and_body_fingerprint": IssueCategory.DUPLICATION,
    "mixed_top_level_path_prefixes": IssueCategory.CRAWL_EFFICIENCY,
}

_CATEGORY_ALIAS_MAP: dict[str, IssueCategory] = {
    "metadata": IssueCategory.METADATA,
    "content": IssueCategory.CONTENT_QUALITY,
    "indexability": IssueCategory.INDEXABILITY,
    "canonical": IssueCategory.DUPLICATION,
    "links": IssueCategory.INTERNAL_LINKING,
    "url_structure": IssueCategory.CRAWL_EFFICIENCY,
    "duplicates": IssueCategory.DUPLICATION,
}

_SEVERITY_SCORE: dict[str, int] = {"info": 5, "low": 15, "medium": 35, "high": 60, "critical": 90}
_CONFIDENCE_SCORE: dict[str, int] = {"low": 8, "medium": 16, "high": 24}


def normalize_issue_category(issue: dict) -> IssueCategory:
    issue_id = str(issue.get("id") or "").strip()
    if issue_id and issue_id in _ID_CATEGORY_MAP:
        return _ID_CATEGORY_MAP[issue_id]
    raw = str(issue.get("category") or "").strip().lower()
    if raw in _CATEGORY_ALIAS_MAP:
        return _CATEGORY_ALIAS_MAP[raw]
    return IssueCategory.TECHNICAL_HEALTH


def normalize_severity(raw: str | None) -> IssueSeverity:
    v = (raw or "").strip().lower()
    if v in ("info", "low", "medium", "high", "critical"):
        return v  # type: ignore[return-value]
    return "low"


def derive_confidence(issue: dict) -> IssueConfidence:
    ev = issue.get("evidence")
    if isinstance(ev, dict) and len(ev) >= 2:
        return "high"
    if isinstance(ev, dict) and len(ev) == 1:
        return "medium"
    return "low"


def derive_priority(
    *,
    severity: IssueSeverity,
    confidence: IssueConfidence,
    inbound_internal: int = 0,
    blast_radius: int = 1,
    recurrence_count: int = 1,
) -> IssuePriority:
    score = _SEVERITY_SCORE.get(severity, 15)
    score += _CONFIDENCE_SCORE.get(confidence, 8)
    score += min(25, max(0, inbound_internal) * 2)
    score += min(35, max(0, blast_radius - 1) * 3)
    score += min(20, max(0, recurrence_count - 1) * 4)
    if score >= 95:
        return "now"
    if score >= 55:
        return "soon"
    return "later"


def recommendation_for_issue(issue_id: str, category: IssueCategory) -> str:
    rid = issue_id.strip().lower()
    if rid in {"missing_title", "short_title", "long_title"}:
        return "Set a clear, unique <title> that matches user intent and SERP snippet constraints."
    if rid == "missing_meta_description":
        return "Add a concise meta description that summarizes the page and improves click-through context."
    if rid in {"missing_h1", "multiple_h1"}:
        return "Ensure exactly one descriptive H1 that aligns with page intent and title."
    if rid in {"missing_canonical", "canonical_mismatch", "multiple_canonical_tags", "duplicate_canonical_tags"}:
        return "Normalize canonical tags so each page has one canonical URL aligned with the preferred indexable URL."
    if rid in {"meta_noindex", "header_noindex", "robots_txt_blocked"}:
        return "Review indexability directives and unblock only pages meant to rank."
    if rid == "non_200_status":
        return "Fix broken status responses or redirect intentionally to a healthy canonical destination."
    if rid in {"orphan_internal", "no_internal_outlinks"}:
        return "Improve internal linking so important pages receive and distribute crawl equity."
    if rid == "deep_url_path":
        return "Consider flattening deep URL paths where feasible to improve crawl efficiency and maintainability."
    if category == IssueCategory.DUPLICATION:
        return "Consolidate duplicate variants with canonicalization, redirects, or content differentiation."
    if category == IssueCategory.CONTENT_QUALITY:
        return "Improve on-page structure and content clarity for search intent and consistency."
    return "Review this issue in context and apply the smallest safe fix that improves crawl and index quality."


def issue_to_insight(
    issue: dict,
    *,
    inbound_internal: int = 0,
    blast_radius: int = 1,
    recurrence_count: int = 1,
) -> InspectorInsight:
    category = normalize_issue_category(issue)
    severity = normalize_severity(str(issue.get("severity") or "low"))
    confidence = derive_confidence(issue)
    priority = derive_priority(
        severity=severity,
        confidence=confidence,
        inbound_internal=inbound_internal,
        blast_radius=blast_radius,
        recurrence_count=recurrence_count,
    )
    summary = str(issue.get("message") or issue.get("id") or "Issue detected")
    evidence_raw = issue.get("evidence")
    evidence: list[EvidenceItem] = []
    if isinstance(evidence_raw, dict):
        for k, v in list(evidence_raw.items())[:8]:
            evidence.append(EvidenceItem(key=str(k), value=str(v)))
    issue_id = str(issue.get("id") or "")
    why = f"Category: {category.value.replace('_', ' ')}. Severity: {severity}. Priority: {priority}."
    rec = recommendation_for_issue(issue_id, category)
    return InspectorInsight(
        category=category.value,
        severity=severity,
        priority=priority,
        confidence=confidence,
        summary=summary,
        why_it_matters=why,
        evidence=evidence,
        recommendation=rec,
        action_label="Open in Audit" if priority in ("soon", "now") else None,
        action_target="audit",
    )


def build_insights(
    issues: list[dict],
    *,
    inbound_internal: int = 0,
    blast_radius_by_issue_id: dict[str, int] | None = None,
) -> list[InspectorInsight]:
    counts: dict[str, int] = {}
    for it in issues:
        iid = str(it.get("id") or "unknown")
        counts[iid] = counts.get(iid, 0) + 1
    out: list[InspectorInsight] = []
    for it in issues:
        iid = str(it.get("id") or "unknown")
        out.append(
            issue_to_insight(
                it,
                inbound_internal=inbound_internal,
                blast_radius=(blast_radius_by_issue_id or {}).get(iid, 1),
                recurrence_count=counts.get(iid, 1),
            )
        )
    order = {"now": 0, "soon": 1, "later": 2}
    out.sort(key=lambda x: (order.get(x.priority, 9), -_SEVERITY_SCORE.get(x.severity, 0)))
    return out
