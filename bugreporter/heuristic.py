"""Offline, rule-based extractor. Deterministic, no network, no API key.

Understands English and a few common Turkish phrasings.
"""

from __future__ import annotations

import re

from .models import BugReport, Environment, Severity

_SEVERITY_RULES: list[tuple[Severity, tuple[str, ...]]] = [
    (Severity.critical, ("data loss", "security", "leak", "everyone", "all users", "outage", "down",
                         "payment", "charged twice", "veri kayb", "güvenlik", "ödeme")),
    (Severity.high, ("crash", "500", "exception", "cannot", "can't", "unable", "blocked", "freez",
                     "not working", "doesn't work", "çöküyor", "çöktü", "açılmıyor", "çalışmıyor")),
    (Severity.low, ("typo", "cosmetic", "misaligned", "alignment", "color", "colour", "spacing",
                    "font", "yazım", "hizala")),
]

_LABEL_RULES: dict[str, tuple[str, ...]] = {
    "auth": ("login", "log in", "sign in", "password", "logout", "session", "giriş", "şifre"),
    "payment": ("payment", "checkout", "card", "charged", "ödeme"),
    "ui": ("button", "layout", "css", "misaligned", "typo", "font", "modal", "page", "buton"),
    "api": ("api", "endpoint", "500", "404", "request", "response", "json"),
    "performance": ("slow", "timeout", "lag", "freez", "yavaş"),
    "mobile": ("ios", "android", "iphone", "mobile", "mobil"),
    "crash": ("crash", "exception", "çöküyor", "çöktü"),
}

_BROWSER = re.compile(r"\b(chrome|firefox|safari|edge|opera)(?:\s*v?(\d+(?:\.\d+)*))?", re.I)
_OS = re.compile(r"\b(windows\s*\d*|mac\s?os(?:\s*\d+)?|ios\s*\d*|android\s*\d*|ubuntu|linux)\b", re.I)
_DEVICE = re.compile(r"\b(iphone\s*\d*(?:\s*pro)?|pixel\s*\d+|galaxy\s*\w+|ipad)\b", re.I)
_VERSION = re.compile(r"\b(?:version|ver|v|build|sürüm)\s*[:#]?\s*(\d+(?:\.\d+)+)\b", re.I)
_STEP_LINE = re.compile(r"^\s*(?:\d+[.)]|[-*•]|step\s*\d+:?)\s*(.+)$", re.I)
_EXPECTED = re.compile(r"^\s*(?:expected|should|beklenen|olması gereken)\s*[:\-]?\s*(.+)$", re.I)
_ACTUAL = re.compile(r"^\s*(?:actual(?:ly)?|instead|but|result|olan|gerçekleşen)\s*[:\-]?\s*(.+)$", re.I)
_COMPONENTS = ("checkout", "login", "cart", "search", "profile", "dashboard", "settings", "api",
               "signup", "payment", "upload", "notifications")


def _clean_title(line: str) -> str:
    title = re.sub(r"^(bug|issue|hata)\s*[:\-]\s*", "", line.strip(), flags=re.I).rstrip(".!")
    title = title[0].upper() + title[1:] if title else "Untitled bug"
    return title if len(title) <= 80 else title[:77].rstrip() + "..."


def _severity(text: str) -> Severity:
    lower = text.lower()
    for severity, words in _SEVERITY_RULES:
        if any(w in lower for w in words):
            return severity
    return Severity.medium


def _environment(text: str) -> Environment:
    browser = _BROWSER.search(text)
    os_match = _OS.search(text)
    device = _DEVICE.search(text)
    version = _VERSION.search(text)
    return Environment(
        browser=" ".join(p for p in (browser.group(1).title(), browser.group(2)) if p) if browser else None,
        os=os_match.group(1).strip() if os_match else None,
        device=device.group(1).strip() if device else None,
        app_version=version.group(1) if version else None,
    )


def _steps(lines: list[str]) -> list[str]:
    steps = []
    for line in lines:
        match = _STEP_LINE.match(line)
        if match and not (_EXPECTED.match(match.group(1)) or _ACTUAL.match(match.group(1))):
            steps.append(match.group(1).strip().rstrip("."))
    if steps:
        return steps
    # Fallback: "open X -> click Y -> see Z" or "then"-chains on one line.
    for line in lines:
        parts = re.split(r"\s*(?:->|→|=>|, then | then | sonra )\s*", line, flags=re.I)
        if len(parts) >= 2:
            return [p.strip().rstrip(".") for p in parts if p.strip()]
    return []


def _first(pattern: re.Pattern[str], lines: list[str]) -> str | None:
    for line in lines:
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return None


def extract(notes: str) -> BugReport:
    """Turn free-form notes into a BugReport using keyword rules."""
    lines = [line for line in notes.splitlines() if line.strip()]
    if not lines:
        raise ValueError("notes are empty")

    lower = notes.lower()
    report = BugReport(
        title=_clean_title(lines[0]),
        severity=_severity(notes),
        component=next((c for c in _COMPONENTS if c in lower), None),
        environment=_environment(notes),
        steps_to_reproduce=_steps(lines[1:] or lines),
        expected=_first(_EXPECTED, lines),
        actual=_first(_ACTUAL, lines),
        labels=sorted(label for label, words in _LABEL_RULES.items() if any(w in lower for w in words)),
    )
    report.missing_info = missing_info(report)
    return report


def missing_info(report: BugReport) -> list[str]:
    """Questions a triager would ask before picking the bug up."""
    questions = []
    if not report.steps_to_reproduce:
        questions.append("What exact steps reproduce the problem?")
    if not report.expected:
        questions.append("What did you expect to happen?")
    if not report.actual:
        questions.append("What happened instead (error message, screenshot)?")
    env = report.environment
    if not (env.browser or env.os or env.device):
        questions.append("Which browser / OS / device was used?")
    return questions
