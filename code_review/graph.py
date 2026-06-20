"""The LangGraph wiring.

Topology:

                 ┌──────────────┐
            ┌───▶│  bug_agent   │───┐
            │    └──────────────┘   │
  START ────┼───▶│ security_agent│──┼──▶ orchestrator ──▶ END
            │    └──────────────┘   │
            └───▶│  test_agent  │───┘
                 └──────────────┘

The three agents run in the same LangGraph superstep (parallel). Each writes to a
*distinct* state key, so there are no concurrent-write conflicts and no reducers
are needed. The orchestrator has three inbound edges, so LangGraph only runs it
once all three agents have finished.
"""

from __future__ import annotations

from typing import TypedDict

from langchain_core.runnables import Runnable
from langgraph.graph import END, START, StateGraph

from .models import Finding, ReviewReport
from .report import build_report


class ReviewState(TypedDict, total=False):
    filename: str
    code: str
    bug_findings: list[Finding]
    security_findings: list[Finding]
    test_findings: list[Finding]
    report: ReviewReport


def _force_category(findings: list[Finding], category: str) -> list[Finding]:
    """Guarantee category integrity regardless of what the model returned."""
    for f in findings:
        f.category = category  # type: ignore[assignment]
    return findings


def build_graph(analyzers: dict[str, Runnable]):
    """Compile the review graph from a dict of three analyzer Runnables."""

    bug_agent = analyzers["bug"]
    security_agent = analyzers["security"]
    test_agent = analyzers["test_coverage"]

    def bug_node(state: ReviewState) -> dict:
        out = bug_agent.invoke({"filename": state["filename"], "code": state["code"]})
        return {"bug_findings": _force_category(out.findings, "bug")}

    def security_node(state: ReviewState) -> dict:
        out = security_agent.invoke(
            {"filename": state["filename"], "code": state["code"]}
        )
        return {"security_findings": _force_category(out.findings, "security")}

    def test_node(state: ReviewState) -> dict:
        out = test_agent.invoke({"filename": state["filename"], "code": state["code"]})
        return {"test_findings": _force_category(out.findings, "test_coverage")}

    def orchestrator_node(state: ReviewState) -> dict:
        combined = (
            state.get("bug_findings", [])
            + state.get("security_findings", [])
            + state.get("test_findings", [])
        )
        report = build_report(state["filename"], combined)
        return {"report": report}

    graph = StateGraph(ReviewState)
    graph.add_node("bug_agent", bug_node)
    graph.add_node("security_agent", security_node)
    graph.add_node("test_agent", test_node)
    graph.add_node("orchestrator", orchestrator_node)

    # Fan out from START to all three specialists.
    graph.add_edge(START, "bug_agent")
    graph.add_edge(START, "security_agent")
    graph.add_edge(START, "test_agent")

    # Fan in to the orchestrator.
    graph.add_edge("bug_agent", "orchestrator")
    graph.add_edge("security_agent", "orchestrator")
    graph.add_edge("test_agent", "orchestrator")
    graph.add_edge("orchestrator", END)

    return graph.compile()


def review_code(graph, filename: str, code: str) -> ReviewReport:
    """Convenience runner: invoke the graph and return the report."""
    result = graph.invoke({"filename": filename, "code": code})
    return result["report"]
