"""Unit tests for the pure report functions (no graph involved)."""

from __future__ import annotations

from code_review.models import Finding
from code_review.report import (
    build_report,
    decide_verdict,
    prioritize,
    render_markdown,
    risk_score,
)


def _f(category, severity, title="x"):
    return Finding(
        category=category,
        severity=severity,
        title=title,
        description="d",
        suggestion="s",
    )


def test_prioritize_orders_by_severity_then_category():
    findings = [
        _f("test_coverage", "low", "low-test"),
        _f("bug", "critical", "crit-bug"),
        _f("security", "high", "high-sec"),
        _f("bug", "high", "high-bug"),
    ]
    ordered = prioritize(findings)
    assert [x.title for x in ordered] == [
        "crit-bug",      # critical wins
        "high-sec",      # high, security before bug (tie-breaker)
        "high-bug",      # high, bug
        "low-test",      # low last
    ]


def test_risk_score_sums_weights():
    findings = [_f("bug", "critical"), _f("security", "high"), _f("bug", "low")]
    # 100 + 40 + 3
    assert risk_score(findings) == 143


def test_verdict_escalates_to_worst_severity():
    assert decide_verdict([_f("bug", "critical")]) == "block"
    assert decide_verdict([_f("bug", "high")]) == "request_changes"
    assert decide_verdict([_f("bug", "medium")]) == "approve_with_nits"
    assert decide_verdict([_f("bug", "low")]) == "approve_with_nits"
    assert decide_verdict([_f("bug", "info")]) == "approve"
    assert decide_verdict([]) == "approve"


def test_build_report_counts_and_sorts():
    findings = [
        _f("bug", "low"),
        _f("security", "critical"),
        _f("test_coverage", "medium"),
    ]
    report = build_report("foo.py", findings)
    assert report.filename == "foo.py"
    assert report.verdict == "block"
    assert report.severity_counts == {"low": 1, "critical": 1, "medium": 1}
    assert report.category_counts == {"bug": 1, "security": 1, "test_coverage": 1}
    # critical security finding must be first
    assert report.findings[0].severity == "critical"


def test_render_markdown_contains_key_sections():
    report = build_report("foo.py", [_f("security", "critical", "RCE")])
    md = render_markdown(report)
    assert "# Code Review" in md
    assert "BLOCK" in md
    assert "RCE" in md
    assert "[CRITICAL]" in md


def test_render_markdown_handles_clean_code():
    report = build_report("foo.py", [])
    md = render_markdown(report)
    assert "No issues found" in md
    assert "APPROVE" in md
