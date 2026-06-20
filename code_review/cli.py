"""Command-line entrypoint.

Examples
--------
    # Review a local file
    uv run code-review --file samples/vulnerable_example.py

    # Review a live public pull request
    uv run code-review --pr psf/requests#6500

    # Pipe code in
    cat foo.py | uv run code-review --stdin --name foo.py
"""

from __future__ import annotations

import argparse
import sys

from .agents import build_analyzers
from .github import fetch_pr_files, parse_pr_ref, review_pr_and_save_markdown
from .graph import build_graph, review_code
from .llm import get_llm
from .report import render_markdown


def _build():
    llm = get_llm()
    analyzers = build_analyzers(llm)
    return build_graph(analyzers)


def _review_one(graph, name: str, code: str) -> None:
    report = review_code(graph, name, code)
    print(render_markdown(report))
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Multi-agent code reviewer.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="Path to a local source file to review.")
    src.add_argument("--pr", help="Public PR reference, e.g. owner/repo#123.")
    src.add_argument("--stdin", action="store_true", help="Read code from stdin.")
    parser.add_argument("--name", default="stdin_input", help="Name for --stdin code.")
    parser.add_argument(
        "--max-files", type=int, default=5, help="Max files to review from a PR."
    )
    args = parser.parse_args(argv)

    if args.pr:
        # Review PR and automatically save to markdown file
        markdown_output = review_pr_and_save_markdown(
            args.pr, max_files=args.max_files
        )
        if markdown_output:
            print(markdown_output)
        return 0 if markdown_output else 1

    graph = _build()

    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            _review_one(graph, args.file, fh.read())
    elif args.stdin:
        _review_one(graph, args.name, sys.stdin.read())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
