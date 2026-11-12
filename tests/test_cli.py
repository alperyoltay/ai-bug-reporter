import io
import json

import pytest

from bugreporter import cli, llm
from bugreporter.models import BugReport, Severity


@pytest.fixture(autouse=True)
def no_credentials(monkeypatch):
    for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE"):
        monkeypatch.delenv(var, raising=False)


def test_markdown_from_file(tmp_path, capsys):
    notes = tmp_path / "notes.txt"
    notes.write_text("Cart badge wrong\n1. add item\n2. remove item\nexpected: 0\nactual: 1", encoding="utf-8")
    assert cli.main([str(notes)]) == 0
    out, err = capsys.readouterr()
    assert out.startswith("## Cart badge wrong")
    assert "1. add item" in out
    assert "(engine: offline)" in err


def test_json_from_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("Typo in footer"))
    cli.main(["--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert data["severity"] == "low"
    assert data["missing_info"]


def test_missing_file_and_empty_input(tmp_path, monkeypatch):
    with pytest.raises(SystemExit, match="file not found"):
        cli.main([str(tmp_path / "nope.txt")])
    monkeypatch.setattr("sys.stdin", io.StringIO("   "))
    with pytest.raises(SystemExit, match="empty"):
        cli.main([])


def test_too_long_input_rejected(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("a" * (cli.MAX_INPUT_CHARS + 1)))
    with pytest.raises(SystemExit, match="longer than"):
        cli.main([])


def test_auto_falls_back_when_ai_fails(monkeypatch, capsys):
    def broken(_notes):
        raise llm.LLMUnavailable("no network")

    monkeypatch.setattr(llm, "extract", broken)
    report, engine = cli.build_report("Login broken", "auto")
    assert engine == "offline"
    assert "using offline rules" in capsys.readouterr().err


def test_claude_engine_uses_ai(monkeypatch):
    monkeypatch.setattr(llm, "extract", lambda _n: BugReport(title="From AI", severity=Severity.low))
    report, engine = cli.build_report("anything", "claude")
    assert (report.title, engine) == ("From AI", "claude")


def test_claude_engine_does_not_silently_fall_back(monkeypatch):
    monkeypatch.setattr(llm, "extract", lambda _n: (_ for _ in ()).throw(llm.LLMUnavailable("declined")))
    with pytest.raises(SystemExit, match="declined"):
        cli.build_report("anything", "claude")
