"""Claude-powered extractor using structured outputs.

Requires the optional dependency: pip install "ai-bug-reporter[ai]"
and credentials (ANTHROPIC_API_KEY, or an `ant auth login` profile).
"""

from __future__ import annotations

from typing import Any

from .models import BugReport

MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = """You turn a tester's rough bug notes into a clean, structured bug report.

Rules:
- Use only facts present in the notes. Never invent versions, devices, URLs or error messages.
- Anything a developer would need to reproduce the bug but the notes do not state goes into
  `missing_info` as a short question to the reporter.
- Steps are ordered, start with a verb, one action each.
- The notes may be in English or Turkish; always write the report in English.
- Severity: critical = data loss, security, payments or the whole app down; high = a main
  feature is broken with no workaround; medium = broken with a workaround; low = cosmetic."""


class LLMUnavailable(RuntimeError):
    """The AI engine cannot run (SDK missing, no credentials, or the model declined)."""


def _client() -> Any:
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - exercised manually
        raise LLMUnavailable('install the AI extra: pip install "ai-bug-reporter[ai]"') from exc
    return anthropic.Anthropic()


def extract(notes: str, client: Any | None = None) -> BugReport:
    """Ask Claude for a BugReport. `client` can be injected for tests."""
    if not notes.strip():
        raise ValueError("notes are empty")
    client = client or _client()

    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"<notes>\n{notes}\n</notes>"}],
        output_format=BugReport,
        output_config={"effort": "low"},  # short extraction task; low effort is plenty
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # if the model declines, the API retries on a fallback model
    )

    if response.stop_reason == "refusal":
        raise LLMUnavailable("the model declined to process these notes")
    if response.stop_reason == "max_tokens" or response.parsed_output is None:
        raise LLMUnavailable("the model did not return a complete report")
    return response.parsed_output
