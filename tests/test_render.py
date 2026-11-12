from bugreporter.models import BugReport, Environment, Severity
from bugreporter.render import to_markdown


def test_full_report_markdown():
    md = to_markdown(BugReport(
        title="Login fails",
        severity=Severity.critical,
        component="login",
        environment=Environment(browser="Safari 17", os="macOS 14"),
        steps_to_reproduce=["Open /login", "Submit valid credentials"],
        expected="Dashboard opens",
        actual="Spinner forever",
        labels=["auth"],
        missing_info=["Does it happen in private mode?"],
    ))
    assert md.startswith("## Login fails")
    assert "🔴 critical" in md
    assert "1. Open /login\n2. Submit valid credentials" in md
    assert "| Browser | Safari 17 |" in md
    assert "- [ ] Does it happen in private mode?" in md


def test_empty_sections_are_marked():
    md = to_markdown(BugReport(title="Vague bug", severity=Severity.medium))
    assert md.count("_Not provided_") == 3
    assert "### Environment" not in md
