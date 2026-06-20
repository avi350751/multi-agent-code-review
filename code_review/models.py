"""Typed data models shared across agents, the orchestrator and the report.

Everything the agents emit is structured (no free-text parsing), which keeps the
graph deterministic and makes the orchestrator's job a pure data transformation.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

# Ordered from most to least urgent. Used for sorting and risk scoring.
Severity = Literal["critical", "high", "medium", "low", "info"]
Category = Literal["bug", "security", "test_coverage"]

# A reviewer can only do four things with a PR; map findings onto that vocabulary.
Verdict = Literal["block", "request_changes", "approve_with_nits", "approve"]


class Finding(BaseModel):
    """A single issue raised by one of the specialist agents."""

    category: Category = Field(description="Which agent domain raised this.")
    severity: Severity = Field(description="Impact if shipped as-is.")
    title: str = Field(description="One-line summary, < 80 chars.")
    description: str = Field(description="What is wrong and why it matters.")
    suggestion: str = Field(description="Concrete fix or next step.")
    line_hint: Optional[str] = Field(
        default=None,
        description="Function name or line reference, if identifiable.",
    )


class FindingList(BaseModel):
    """Structured-output container the LLM fills in for each agent."""

    findings: list[Finding] = Field(default_factory=list)


class ReviewReport(BaseModel):
    """The orchestrator's combined, prioritized output."""

    filename: str
    findings: list[Finding]
    severity_counts: dict[str, int]
    category_counts: dict[str, int]
    risk_score: int
    verdict: Verdict
