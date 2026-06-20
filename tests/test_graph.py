"""Integration tests for the end-to-end LangGraph flow.

These drive the compiled graph with deterministic fake agents, so they validate
fan-out -> parallel execution -> fan-in -> orchestration without any LLM call.
"""

from __future__ import annotations

from code_review.graph import review_code
from code_review.models import ReviewReport


def test_flow_produces_report(review_graph, sample_code):
    report = review_code(review_graph, "sample.py", sample_code)
    assert isinstance(report, ReviewReport)
    assert report.filename == "sample.py"


def test_all_three_agents_contribute(review_graph, sample_code):
    report = review_code(review_graph, "sample.py", sample_code)
    categories = {f.category for f in report.findings}
    # Every specialist agent reached the orchestrator and was merged in.
    assert categories == {"bug", "security", "test_coverage"}


def test_orchestrator_prioritizes_critical_first(review_graph, sample_code):
    report = review_code(review_graph, "sample.py", sample_code)
    # The fake security agent raises a critical eval() finding.
    assert report.findings[0].severity == "critical"
    assert report.findings[0].category == "security"


def test_verdict_blocks_on_critical(review_graph, sample_code):
    report = review_code(review_graph, "sample.py", sample_code)
    assert report.verdict == "block"


def test_risk_score_is_positive(review_graph, sample_code):
    report = review_code(review_graph, "sample.py", sample_code)
    assert report.risk_score > 0


def test_clean_code_approves(clean_graph, sample_code):
    report = review_code(clean_graph, "sample.py", sample_code)
    assert report.findings == []
    assert report.verdict == "approve"
    assert report.risk_score == 0


def test_category_integrity_is_enforced(review_graph, sample_code):
    # Every finding carries the category of the agent that produced it.
    report = review_code(review_graph, "sample.py", sample_code)
    for f in report.findings:
        assert f.category in {"bug", "security", "test_coverage"}


def test_graph_node_structure(review_graph):
    # The compiled graph should expose the four nodes we wired.
    nodes = set(review_graph.get_graph().nodes)
    for expected in {"bug_agent", "security_agent", "test_agent", "orchestrator"}:
        assert expected in nodes
