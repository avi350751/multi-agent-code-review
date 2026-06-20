"""Fetch changed files from a public GitHub pull request and generate reviews.

Uses only the standard library. Works unauthenticated for public repos (subject
to GitHub's rate limit); set GITHUB_TOKEN to raise the limit. Returns one
(filename, patch) pair per changed file so each file can be reviewed on its own.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

_PR_RE = re.compile(r"^(?P<owner>[^/]+)/(?P<repo>[^#]+)#(?P<num>\d+)$")


def parse_pr_ref(ref: str) -> tuple[str, str, int]:
    """Parse an 'owner/repo#123' reference."""
    m = _PR_RE.match(ref.strip())
    if not m:
        raise ValueError(f"Expected 'owner/repo#number', got: {ref!r}")
    return m["owner"], m["repo"], int(m["num"])


def _get(url: str) -> bytes:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "code-review-agents",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (trusted host)
        return resp.read()


def fetch_pr_files(
    owner: str, repo: str, number: int, max_files: int = 10
) -> list[tuple[str, str]]:
    """Return [(filename, patch), ...] for the files changed in a PR.

    The 'patch' is the unified diff hunk for that file. Files without a patch
    (e.g. pure binary changes) are skipped.
    """
    url = (
        f"https://api.github.com/repos/{owner}/{repo}"
        f"/pulls/{number}/files?per_page={max_files}"
    )
    data = json.loads(_get(url))
    out: list[tuple[str, str]] = []
    for item in data[:max_files]:
        patch = item.get("patch")
        if patch:
            out.append((item["filename"], patch))
    return out


def review_pr_and_save_markdown(
    pr_ref: str, max_files: int = 5
) -> str:
    """Review a PR and automatically save the output to a markdown file.
    
    Args:
        pr_ref: PR reference (e.g., 'owner/repo#123')
        max_files: Maximum number of files to review
    
    Returns:
        Markdown review output as string
    """
    from .agents import build_analyzers
    from .graph import build_graph, review_code
    from .llm import get_llm
    from .report import render_markdown
    
    owner, repo, num = parse_pr_ref(pr_ref)
    
    # Generate automatic output filename
    output_file = f"pr_review_{owner}_{repo}_{num}.md"
    
    # Fetch PR files
    print(f"📥 Fetching files from {pr_ref}...", file=sys.stderr)
    files = fetch_pr_files(owner, repo, num, max_files=max_files)
    
    if not files:
        print("❌ No reviewable (text) files found in that PR.", file=sys.stderr)
        return ""
    
    # Build review graph
    print(f"🔨 Building review graph...", file=sys.stderr)
    llm = get_llm()
    analyzers = build_analyzers(llm)
    graph = build_graph(analyzers)
    
    # Review files and collect output
    print(f"🔍 Reviewing {len(files)} file(s)...", file=sys.stderr)
    output_parts = [
        f"# Code Review: {pr_ref}",
        f"_Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
    ]
    
    for name, patch in files:
        print(f"  ⏳ Reviewing {name}...", file=sys.stderr)
        report = review_code(graph, name, patch)
        output_parts.append(render_markdown(report))
        output_parts.append("")
    
    markdown_output = "\n".join(output_parts)
    
    # Save to file automatically
    output_path = Path(output_file)
    output_path.write_text(markdown_output, encoding="utf-8")
    print(f"✅ Review saved to {output_file}", file=sys.stderr)
    
    return markdown_output
