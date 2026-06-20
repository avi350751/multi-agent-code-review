"""LLM factory.

Isolated here so the only place that touches the API key is one
small function. Everything else depends on the abstract Runnables.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
load_dotenv()


def get_llm():
    """Return a configured ChatOpenAI model.

    Model is overridable via
    CODE_REVIEW_MODEL. temperature=0 keeps reviews stable across runs.
    """
    from langchain_openai import ChatOpenAI

    model = os.environ.get("CODE_REVIEW_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model, temperature=0, max_tokens=4096)
