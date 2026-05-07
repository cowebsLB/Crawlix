"""Filter option definitions for page builders."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LabeledValue:
    label: str
    value: object


def crawl_http_filter_options() -> tuple[LabeledValue, ...]:
    return (
        LabeledValue("Any", None),
        LabeledValue("2xx", "2xx"),
        LabeledValue("3xx", "3xx"),
        LabeledValue("4xx", "4xx"),
        LabeledValue("5xx", "5xx"),
        LabeledValue("Errors (≥400)", "err"),
        LabeledValue("No status", "none"),
    )


def crawl_depth_filter_options(max_depth: int = 10) -> tuple[LabeledValue, ...]:
    options: list[LabeledValue] = [LabeledValue("Any", None)]
    for depth in range(0, max_depth + 1):
        options.append(LabeledValue(str(depth), depth))
    return tuple(options)


def audit_filter_field_labels() -> tuple[str, str, str]:
    return ("Search URL:", "Max score (≤):", "Min issues (≥):")
