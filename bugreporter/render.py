"""Render a BugReport as GitHub-flavoured Markdown, ready to paste into an issue."""

from __future__ import annotations

from .models import BugReport

_SEVERITY_ICON = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}


def to_markdown(report: BugReport) -> str:
    sev = report.severity.value
    env = report.environment
    env_rows = [(k, v) for k, v in (("Browser", env.browser), ("OS", env.os),
                                    ("Device", env.device), ("App version", env.app_version)) if v]

    out = [f"## {report.title}", ""]
    out.append(f"**Severity:** {_SEVERITY_ICON[sev]} {sev}")
    if report.component:
        out.append(f"**Component:** {report.component}")
    if report.labels:
        out.append("**Labels:** " + ", ".join(f"`{label}`" for label in report.labels))
    out.append("")

    out += ["### Steps to reproduce"]
    out += [f"{i}. {step}" for i, step in enumerate(report.steps_to_reproduce, 1)] or ["_Not provided_"]
    out += ["", "### Expected", report.expected or "_Not provided_",
            "", "### Actual", report.actual or "_Not provided_", ""]

    if env_rows:
        out += ["### Environment", "| | |", "|---|---|"]
        out += [f"| {k} | {v} |" for k, v in env_rows]
        out.append("")

    if report.missing_info:
        out += ["### ❓ Missing information"]
        out += [f"- [ ] {q}" for q in report.missing_info]
        out.append("")

    return "\n".join(out)
