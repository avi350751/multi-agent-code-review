"""Offline demo: run the full graph with deterministic fake agents and print
the rendered review. Requires no API key — useful for seeing the output shape.

    uv run python examples/demo_offline.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from code_review.graph import build_graph, review_code  # noqa: E402
from code_review.report import render_markdown  # noqa: E402
from tests.fakes import fake_analyzers  # noqa: E402

SAMPLE = Path(__file__).resolve().parents[1] / "samples" / "vulnerable_example.py"


def main() -> None:
    code = SAMPLE.read_text(encoding="utf-8")
    graph = build_graph(fake_analyzers())
    report = review_code(graph, "samples/vulnerable_example.py", code)
    print(render_markdown(report))
    print("\n--- machine-readable summary ---")
    print("verdict      :", report.verdict)
    print("risk_score   :", report.risk_score)
    print("by severity  :", report.severity_counts)
    print("by category  :", report.category_counts)


if __name__ == "__main__":
    main()
