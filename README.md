# code-review-agents

An automated code review system that uses **three AI agents** to review code for bugs, security issues, and test coverage gaps.

## How it works

Three specialist agents analyze your code **in parallel**:

| Agent | Looks for |
|-------|-----------|
| **Bug Agent** | Logic errors, resource leaks, bad patterns |
| **Security Agent** | Hardcoded secrets, injection attacks, unsafe code |
| **Test Coverage Agent** | Missing tests, untested edge cases |

They each provide findings, which are combined into a **single report** with a verdict:
- 🔴 **Block** — Critical issues found
- 🟠 **Request Changes** — High severity issues
- 🟡 **Approve with Nits** — Minor issues only
- 🟢 **Approve** — No issues found

## Installation

```bash
uv sync
```

## Usage

### Try it out (no API key needed)
```bash
uv run python examples/demo_offline.py
```

### Review a GitHub PR
```bash
uv run code-review --pr owner/repo#123
```
Example: `uv run code-review --pr psf/requests#6500`

### Review a local file
```bash
uv run code-review --file path/to/file.py
```

### Review code from stdin
```bash
cat file.py | uv run code-review --stdin --name file.py
```

## API Key Setup

For reviewing GitHub PRs:
- **Public repos**: Work without authentication (60 requests/hour per IP)
- **Private repos or higher limits**: Set `GITHUB_TOKEN`
  ```bash
  export GITHUB_TOKEN=your_github_token
  ```

## Testing

Run the test suite:
```bash
uv run pytest
```

Tests validate report logic, verdicts, and the full agent graph with deterministic fake agents.

## Project Structure

```
code_review/
  cli.py        # Command-line interface
  graph.py      # LangGraph orchestration (agents run in parallel)
  agents.py     # System prompts for the 3 agents
  models.py     # Data models (Pydantic)
  report.py     # Report generation and formatting
  llm.py        # LLM configuration
  github.py     # GitHub PR fetching
tests/          # Unit and integration tests
samples/        # Example code to review
examples/       # Demo without API key
```

## How to Extend

Add a new review agent:
1. Write a system prompt in `agents.py`
2. Add the agent to the graph in `graph.py`
3. Update findings categories in `models.py` (optional)

## Under the Hood

- **Parallel processing**: All three agents analyze code simultaneously using LangGraph
- **Structured output**: Each agent returns JSON findings, no text parsing needed
- **Deterministic testing**: Test suite injects fake agents, validates without API calls
- **Severity scoring**: Findings are ranked and combined into a single risk score
