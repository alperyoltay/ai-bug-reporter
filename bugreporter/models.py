"""The structured bug report every engine must produce."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Environment(BaseModel):
    browser: str | None = Field(None, description="Browser and version, e.g. 'Chrome 131'")
    os: str | None = Field(None, description="Operating system, e.g. 'Windows 11', 'iOS 18'")
    device: str | None = Field(None, description="Device type or model if mentioned")
    app_version: str | None = Field(None, description="App/build version if mentioned")


class BugReport(BaseModel):
    title: str = Field(description="Short, specific summary (max ~80 chars), no trailing period")
    severity: Severity = Field(description="Impact on users: critical = data loss/security/outage, low = cosmetic")
    component: str | None = Field(None, description="Affected area, e.g. 'checkout', 'login', 'API'")
    environment: Environment = Field(default_factory=Environment)
    steps_to_reproduce: list[str] = Field(default_factory=list, description="Ordered, one action per step")
    expected: str | None = Field(None, description="What should have happened")
    actual: str | None = Field(None, description="What actually happened")
    labels: list[str] = Field(default_factory=list, description="Lowercase tags such as 'ui', 'auth', 'performance'")
    missing_info: list[str] = Field(
        default_factory=list,
        description="Questions to ask the reporter for anything needed to reproduce that the notes do not say",
    )
