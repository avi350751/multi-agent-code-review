"""Pure functions that turn a flat list of findings into a prioritized report.

Kept free of LangChain/LangGraph imports so it is trivially unit-testable and
reusable outside the graph.
"""

from __future__ import annotations

from .models import Finding, ReviewReport, Verdict

# Lower rank = shown first.
SEVERITY_RANK: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}

# Weights drive a single comparable risk number for the whole change.
SEVERITY_WEIGHT: dict[str, int] = {
    "critical": 100,
    "high": 40,
    "medium": 10,
    "low": 3,
    "info": 1,
}

# Security issues of equal severity should surface above functional bugs,
# which in turn rank above missing-test notes. Used as a tie-breaker only.
CATEGORY_RANK: dict[str, int] = {
    "security": 0,
    "bug": 1,
    "test_coverage": 2,
}


def prioritize(findings: list[Finding]) -> list[Finding]:
    """Sort by severity first, then by category as a tie-breaker."""
    return sorted(
        findings,
        key=lambda f: (SEVERITY_RANK[f.severity], CATEGORY_RANK[f.category]),
    )


def risk_score(findings: list[Finding]) -> int:
    """Single integer summarising overall risk of the change."""
    return sum(SEVERITY_WEIGHT[f.severity] for f in findings)


def decide_verdict(findings: list[Finding]) -> Verdict:
    """Map the worst finding onto a merge decision."""
    severities = {f.severity for f in findings}
    if "critical" in severities:
        return "block"
    if "high" in severities:
        return "request_changes"
    if "medium" in severities or "low" in severities:
        return "approve_with_nits"
    return "approve"


def _count(findings: list[Finding], attr: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for f in findings:
        key = getattr(f, attr)
        counts[key] = counts.get(key, 0) + 1
    return counts


def build_report(filename: str, findings: list[Finding]) -> ReviewReport:
    """Combine raw findings from all agents into the final structured report."""
    ordered = prioritize(findings)
    return ReviewReport(
        filename=filename,
        findings=ordered,
        severity_counts=_count(ordered, "severity"),
        category_counts=_count(ordered, "category"),
        risk_score=risk_score(ordered),
        verdict=decide_verdict(ordered),
    )


_VERDICT_LABEL = {
    "block": "BLOCK — must fix before merge",
    "request_changes": "REQUEST CHANGES",
    "approve_with_nits": "APPROVE WITH NITS",
    "approve": "APPROVE",
}

_SEVERITY_BADGE = {
    "critical": "[CRITICAL]",
    "high": "[HIGH]",
    "medium": "[MEDIUM]",
    "low": "[LOW]",
    "info": "[INFO]",
}


def render_markdown(report: ReviewReport) -> str:
    """Human-readable review suitable for a PR comment."""
    lines: list[str] = []
    lines.append(f"# Code Review — `{report.filename}`")
    lines.append("")
    lines.append(f"**Verdict:** {_VERDICT_LABEL[report.verdict]}  ")
    lines.append(f"**Risk score:** {report.risk_score}  ")

    counts = report.severity_counts
    summary = ", ".join(
        f"{counts[s]} {s}" for s in SEVERITY_RANK if counts.get(s)
    )
    lines.append(f"**Findings:** {summary or 'none'}")
    lines.append("")

    if not report.findings:
        lines.append("_No issues found by any agent._")
        return "\n".join(lines)

    lines.append("## Findings (highest priority first)")
    lines.append("")
    for i, f in enumerate(report.findings, 1):
        badge = _SEVERITY_BADGE[f.severity]
        loc = f" (`{f.line_hint}`)" if f.line_hint else ""
        lines.append(f"### {i}. {badge} {f.title}{loc}")
        lines.append(f"- **Category:** {f.category}")
        lines.append(f"- **Why:** {f.description}")
        lines.append(f"- **Fix:** {f.suggestion}")
        lines.append("")

    return "\n".join(lines)
