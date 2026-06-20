"""The three specialist agents.

Each agent is just a `prompt | structured_llm` Runnable that takes
`{"filename", "code"}` and returns a `FindingList`. Building them through a
factory means the graph depends on *Runnables*, not on a concrete LLM — so tests
can inject deterministic fakes (see tests/fakes.py) without any network calls.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from .models import FindingList

_HUMAN_TEMPLATE = "File under review: {filename}\n\n```\n{code}\n```"


def _make_analyzer(llm: BaseChatModel, system_prompt: str) -> Runnable:
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", _HUMAN_TEMPLATE)]
    )
    return prompt | llm.with_structured_output(FindingList)


BUG_SYSTEM = """You are a senior engineer reviewing code for correctness bugs and \
anti-patterns. Look for: logic errors, off-by-one mistakes, unhandled None/null, \
mutable default arguments, resource leaks (unclosed files/sockets), race conditions, \
incorrect error handling, dead code, and violations of idiomatic style that will \
cause maintenance pain.

Only report real, defensible issues — do NOT invent problems to look thorough. \
For each issue set severity by real-world impact:
- critical: crashes or data corruption on a common path
- high: incorrect results or failures on realistic inputs
- medium: latent bug or fragile code likely to break later
- low: minor correctness/readability concern
- info: stylistic nit

Set every finding's category to "bug"."""

SECURITY_SYSTEM = """You are an application security reviewer. Look for: injection \
(SQL/command/template), use of eval/exec on untrusted input, hardcoded secrets or \
credentials, weak crypto or hashing, insecure deserialization (pickle/yaml.load), \
path traversal, SSRF, missing authn/authz checks, unsafe subprocess/shell usage, and \
sensitive data logged in plaintext.

Only report genuine, exploitable weaknesses. Severity guidance:
- critical: remotely exploitable RCE, auth bypass, or credential leak
- high: injection or sensitive-data exposure exploitable with some conditions
- medium: weak crypto / insecure default / hardening gap
- low: defense-in-depth improvement
- info: informational note

Set every finding's category to "security"."""

TEST_SYSTEM = """You are a test engineer assessing test coverage for the code under \
review. Identify untested behaviour the team should add tests for: happy paths, edge \
cases (empty/None/boundary values), error/exception branches, and security-relevant \
inputs. If the file itself looks like production code with no tests, say so.

Each finding's title should name the missing test and the suggestion should describe \
the concrete test case to write. Severity reflects how risky the untested behaviour is:
- high: untested error handling or security-relevant branch
- medium: untested edge case on a core path
- low: missing happy-path or nice-to-have test
- info: coverage observation

Set every finding's category to "test_coverage"."""


def build_analyzers(llm: BaseChatModel) -> dict[str, Runnable]:
    """Construct the three production analyzers from a single chat model."""
    return {
        "bug": _make_analyzer(llm, BUG_SYSTEM),
        "security": _make_analyzer(llm, SECURITY_SYSTEM),
        "test_coverage": _make_analyzer(llm, TEST_SYSTEM),
    }
