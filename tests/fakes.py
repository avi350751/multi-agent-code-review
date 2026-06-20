"""Deterministic stand-ins for the LLM-backed analyzers.

Each fake is a RunnableLambda with the same interface as a real analyzer:
input  -> {"filename": str, "code": str}
output -> FindingList

This lets the test suite exercise the *entire* LangGraph flow — fan-out,
parallel execution, fan-in, orchestration, scoring and rendering — without an
API key or any network access.
"""

from __future__ import annotations

from langchain_core.runnables import Runnable, RunnableLambda

from code_review.models import Finding, FindingList


def _bug(inputs: dict) -> FindingList:
    triggered = "basket=[]" in inputs["code"] or "open(" in inputs["code"]
    findings = []
    if triggered:
        findings.append(
            Finding(
                category="bug",
                severity="high",
                title="Mutable default argument",
                description="Default list is shared across calls.",
                suggestion="Use None and create the list inside the function.",
                line_hint="add_item",
            )
        )
    return FindingList(findings=findings)


def _security(inputs: dict) -> FindingList:
    findings = []
    if "eval(" in inputs["code"]:
        findings.append(
            Finding(
                category="security",
                severity="critical",
                title="eval() on untrusted input",
                description="Allows arbitrary code execution.",
                suggestion="Parse with json.loads or ast.literal_eval.",
                line_hint="load_config",
            )
        )
    if "%s" in inputs["code"]:
        findings.append(
            Finding(
                category="security",
                severity="high",
                title="SQL injection",
                description="Username is interpolated into the query string.",
                suggestion="Use parameterised queries.",
                line_hint="get_user",
            )
        )
    return FindingList(findings=findings)


def _test_cov(inputs: dict) -> FindingList:
    return FindingList(
        findings=[
            Finding(
                category="test_coverage",
                severity="medium",
                title="No tests for get_user",
                description="Error and empty-result branches are untested.",
                suggestion="Add tests for a missing user and a malformed name.",
                line_hint="get_user",
            )
        ]
    )


def fake_analyzers() -> dict[str, Runnable]:
    return {
        "bug": RunnableLambda(_bug),
        "security": RunnableLambda(_security),
        "test_coverage": RunnableLambda(_test_cov),
    }


def empty_analyzers() -> dict[str, Runnable]:
    """All agents return nothing — for the clean-code / approve path."""
    blank = RunnableLambda(lambda _inputs: FindingList(findings=[]))
    return {"bug": blank, "security": blank, "test_coverage": blank}
