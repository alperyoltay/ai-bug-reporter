"""The Claude client is mocked: these tests check what we send and how we handle replies."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from bugreporter import llm
from bugreporter.models import BugReport, Severity

REPORT = BugReport(title="Login fails on Safari", severity=Severity.high)


def fake_client(stop_reason="end_turn", parsed=REPORT):
    client = MagicMock()
    client.beta.messages.parse.return_value = SimpleNamespace(stop_reason=stop_reason, parsed_output=parsed)
    return client


def test_sends_structured_output_request():
    client = fake_client()
    assert llm.extract("login broken on safari", client=client) == REPORT

    kwargs = client.beta.messages.parse.call_args.kwargs
    assert kwargs["model"] == "claude-opus-5-5"
    assert kwargs["output_format"] is BugReport
    assert kwargs["fallbacks"] == "default"
    assert "<notes>\nlogin broken on safari\n</notes>" in kwargs["messages"][0]["content"]
    assert "Never invent" in kwargs["system"]


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_unusable_replies_raise(stop_reason):
    with pytest.raises(llm.LLMUnavailable):
        llm.extract("notes", client=fake_client(stop_reason=stop_reason))


def test_missing_parsed_output_raises():
    with pytest.raises(llm.LLMUnavailable):
        llm.extract("notes", client=fake_client(parsed=None))


def test_empty_notes_never_call_the_api():
    client = fake_client()
    with pytest.raises(ValueError):
        llm.extract("  ", client=client)
    client.beta.messages.parse.assert_not_called()
