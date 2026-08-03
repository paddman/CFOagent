from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Mapping, Sequence

from .models import JournalLine, ZERO, decimal_json, money


def validate_journal(
    lines: Sequence[JournalLine], *, tolerance: Decimal = Decimal("0.01")
) -> dict[str, object]:
    if len(lines) < 2:
        raise ValueError("a journal requires at least two lines")
    errors: list[str] = []
    total_debit = ZERO
    total_credit = ZERO
    for index, line in enumerate(lines, start=1):
        if line.debit < ZERO or line.credit < ZERO:
            errors.append(f"line {index}: debit and credit must not be negative")
        if line.debit > ZERO and line.credit > ZERO:
            errors.append(f"line {index}: cannot contain both debit and credit")
        if line.debit == ZERO and line.credit == ZERO:
            errors.append(f"line {index}: requires debit or credit")
        total_debit += line.debit
        total_credit += line.credit
    difference = total_debit - total_credit
    balanced = abs(difference) <= tolerance and not errors
    if abs(difference) > tolerance:
        errors.append(f"journal is out of balance by {difference}")
    return decimal_json(
        {
            "balanced": balanced,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "difference": difference,
            "line_count": len(lines),
            "errors": errors,
        }
    )


def reconcile_balances(
    ledger: Mapping[str, Decimal | int | float | str],
    subledger: Mapping[str, Decimal | int | float | str],
    *,
    tolerance: Decimal = Decimal("0.01"),
) -> list[dict[str, object]]:
    accounts = sorted(set(ledger) | set(subledger))
    output = []
    for account in accounts:
        ledger_value = money(ledger.get(account))
        subledger_value = money(subledger.get(account))
        difference = ledger_value - subledger_value
        output.append(
            decimal_json(
                {
                    "account": account,
                    "ledger": ledger_value,
                    "subledger": subledger_value,
                    "difference": difference,
                    "reconciled": abs(difference) <= tolerance,
                }
            )
        )
    return output


def close_checklist(period: str) -> list[dict[str, str]]:
    if not period.strip():
        raise ValueError("period is required")
    tasks = [
        "Lock subledgers and validate interfaces",
        "Complete bank reconciliations",
        "Complete AR and AP reconciliations",
        "Review accruals, prepayments, and provisions",
        "Validate fixed assets, depreciation, and leases",
        "Run intercompany matching and elimination checks",
        "Review tax reconciliations and deferred tax",
        "Perform analytical review and flux investigation",
        "Complete disclosure and reporting checklist",
        "Obtain preparer and reviewer sign-off",
    ]
    return [
        {"period": period, "task": task, "status": "open", "owner": "unassigned"}
        for task in tasks
    ]


def aging_bucket(days_past_due: int) -> str:
    if days_past_due <= 0:
        return "current"
    if days_past_due <= 30:
        return "1-30"
    if days_past_due <= 60:
        return "31-60"
    if days_past_due <= 90:
        return "61-90"
    return "90+"
