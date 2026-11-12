"""ai-bug-reporter: turn messy bug notes into structured bug reports."""

from .models import BugReport, Environment, Severity

__all__ = ["BugReport", "Environment", "Severity"]
__version__ = "0.1.0"
