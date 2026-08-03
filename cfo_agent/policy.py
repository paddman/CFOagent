from __future__ import annotations

import re
from typing import Iterable

from .models import PolicyDecision


READ_ONLY_ACTIONS = {
    "analyze",
    "forecast",
    "reconcile",
    "classify",
    "draft",
    "simulate",
    "query",
    "summarize",
    "report",
    "review",
}

HUMAN_APPROVAL_ACTIONS = {
    "payment-release",
    "payment release",
    "journal-posting",
    "journal posting",
    "tax-submission",
    "tax submission",
    "payroll-release",
    "payroll release",
    "vendor-bank-change",
    "vendor bank change",
    "trade-execution",
    "trade execution",
    "contract-signing",
    "contract signing",
    "external-publication",
    "external publication",
}

BLOCKED_ACTIONS = {
    "bypass-approval",
    "bypass approval",
    "disable-audit",
    "disable audit",
    "disable audit log",
    "fabricate-evidence",
    "fabricate evidence",
    "hide-transaction",
    "hide transaction",
}


def normalize_action(action: str) -> str:
    return " ".join(action.lower().strip().replace("_", " ").split())


def evaluate_action(action: str, *, authorized: bool = False) -> PolicyDecision:
    normalized = normalize_action(action)
    if normalized in BLOCKED_ACTIONS:
        return PolicyDecision(
            action=action,
            allowed=False,
            requires_human=True,
            reason="action violates the audit and governance boundary",
        )
    if normalized in HUMAN_APPROVAL_ACTIONS:
        return PolicyDecision(
            action=action,
            allowed=authorized,
            requires_human=True,
            reason=(
                "authorized human approval recorded"
                if authorized
                else "authorized human approval is required"
            ),
        )
    if normalized in READ_ONLY_ACTIONS:
        return PolicyDecision(
            action=action,
            allowed=True,
            requires_human=False,
            reason="read-only analytical action",
        )
    return PolicyDecision(
        action=action,
        allowed=False,
        requires_human=True,
        reason="unknown action requires policy-owner review",
    )


def redact_sensitive(text: str) -> str:
    patterns: Iterable[tuple[re.Pattern[str], str]] = (
        (
            re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
            "[REDACTED_EMAIL]",
        ),
        (re.compile(r"\b\d{10,16}\b"), "[REDACTED_ACCOUNT]"),
        (re.compile(r"(?i)(api[_ -]?key|secret|token)\s*[:=]\s*\S+"), r"\1=[REDACTED]"),
    )
    output = text
    for pattern, replacement in patterns:
        output = pattern.sub(replacement, output)
    return output
