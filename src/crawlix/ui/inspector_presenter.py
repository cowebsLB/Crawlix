from __future__ import annotations

from crawlix.services.analyzer.insights import InspectorInsight


def insights_to_plain_text(insights: list[InspectorInsight]) -> str:
    if not insights:
        return "No issues detected for this selection."
    lines: list[str] = []
    for i, ins in enumerate(insights[:10], start=1):
        lines.append(f"{i}. [{ins.priority.upper()} · {ins.severity.upper()} · {ins.category}] {ins.summary}")
        lines.append(f"   Why: {ins.why_it_matters}")
        if ins.evidence:
            ev = "; ".join(f"{e.key}={e.value}" for e in ins.evidence[:4])
            lines.append(f"   Evidence: {ev}")
        lines.append(f"   Fix: {ins.recommendation}")
    return "\n".join(lines)
