"""Command line entry point: `bugreport notes.txt` or `cat notes.txt | bugreport`."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import heuristic
from .models import BugReport
from .render import to_markdown

MAX_INPUT_CHARS = 20_000


def _read_input(path: str | None) -> str:
    if path in (None, "-"):
        text = sys.stdin.read()
    else:
        file = Path(path)
        if not file.is_file():
            raise SystemExit(f"error: file not found: {path}")
        text = file.read_text(encoding="utf-8")
    if len(text) > MAX_INPUT_CHARS:
        raise SystemExit(f"error: notes are longer than {MAX_INPUT_CHARS} characters")
    return text


def build_report(notes: str, engine: str) -> tuple[BugReport, str]:
    """Return the report and the engine that produced it."""
    if engine == "offline":
        return heuristic.extract(notes), "offline"

    from . import llm

    try:
        return llm.extract(notes), "claude"
    except llm.LLMUnavailable as exc:
        if engine == "claude":
            raise SystemExit(f"error: {exc}")
        print(f"note: AI engine unavailable ({exc}); using offline rules", file=sys.stderr)
        return heuristic.extract(notes), "offline"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bugreport", description="Turn messy bug notes into a clean bug report.")
    parser.add_argument("file", nargs="?", help="notes file (default: stdin)")
    parser.add_argument("-e", "--engine", choices=["auto", "claude", "offline"], default="auto",
                        help="auto = Claude when credentials exist, else offline rules")
    parser.add_argument("-f", "--format", choices=["md", "json"], default="md")
    args = parser.parse_args(argv)

    # Windows consoles often default to a legacy code page (e.g. cp1254) that cannot print emoji.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    notes = _read_input(args.file)
    if not notes.strip():
        raise SystemExit("error: notes are empty")

    engine = args.engine
    if engine == "auto" and not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
                                 or os.getenv("ANTHROPIC_PROFILE")):
        engine = "offline"

    report, used = build_report(notes, engine)
    if args.format == "json":
        print(report.model_dump_json(indent=2))
    else:
        print(to_markdown(report))
    print(f"(engine: {used})", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
