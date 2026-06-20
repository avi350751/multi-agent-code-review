"""Shared fixtures."""

from __future__ import annotations

import pytest

from code_review.graph import build_graph
from tests.fakes import empty_analyzers, fake_analyzers

SAMPLE_CODE = """
API_TOKEN = "sk-live-secret"

def add_item(item, basket=[]):
    basket.append(item)
    return basket

def get_user(db, name):
    cur.execute("SELECT * FROM users WHERE name = '%s'" % name)

def load_config(raw):
    return eval(raw)

def read_log(path):
    f = open(path)
    return f.read()
"""


@pytest.fixture
def review_graph():
    """Graph wired with deterministic fake agents."""
    return build_graph(fake_analyzers())


@pytest.fixture
def clean_graph():
    """Graph where every agent reports no issues."""
    return build_graph(empty_analyzers())


@pytest.fixture
def sample_code() -> str:
    return SAMPLE_CODE
