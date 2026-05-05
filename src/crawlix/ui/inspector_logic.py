"""Pure UI inspector logic helpers extracted from MainWindow."""

from __future__ import annotations


def crawl_pseudo_issues(*, status_code: int | None, depth: int | None, inbound: int, outbound: int) -> list[dict]:
    out: list[dict] = []
    if status_code is not None and int(status_code) >= 400:
        out.append(
            {
                "id": "non_200_status",
                "severity": "high",
                "message": f"HTTP status is {int(status_code)}.",
                "evidence": {"status_code": int(status_code)},
            }
        )
    if inbound == 0 and (depth is not None and int(depth) > 0):
        out.append(
            {
                "id": "orphan_internal",
                "severity": "medium",
                "message": "No internal inbound links.",
                "evidence": {},
            }
        )
    if outbound == 0:
        out.append(
            {
                "id": "no_internal_outlinks",
                "severity": "low",
                "message": "No internal outbound links.",
                "evidence": {},
            }
        )
    return out


def serp_pseudo_issues(*, status: str, organic_rows: int) -> list[dict]:
    out: list[dict] = []
    if organic_rows == 0:
        out.append(
            {
                "id": "crawl_efficiency_sparse_serp",
                "severity": "medium",
                "message": "No organic rows parsed.",
            }
        )
    if status != "ok":
        out.append(
            {
                "id": "technical_health_serp_status",
                "severity": "high",
                "message": "SERP snapshot status is not OK.",
            }
        )
    return out


def citation_pseudo_issues(*, status: str, http_status: int | None) -> list[dict]:
    out: list[dict] = []
    if status != "ok":
        sev = "high" if status == "error" else "medium"
        out.append(
            {
                "id": "technical_health_citation_status",
                "severity": sev,
                "message": f"Citation check status: {status}.",
            }
        )
    if isinstance(http_status, int) and http_status >= 400:
        out.append(
            {
                "id": "technical_health_citation_http",
                "severity": "high",
                "message": f"HTTP {http_status} from citation source.",
            }
        )
    return out
